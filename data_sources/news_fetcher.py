from datetime import datetime, timezone
import html
import os
import socket
import subprocess
from typing import Optional
import xml.etree.ElementTree as ET

import pandas as pd
import requests

from config.constants import REQUIRED_RAW_NEWS_COLUMNS

from .keyword_mapper import map_news_keywords
from .source_loader import load_raw_news, load_unified_sources, save_raw_news
from .utils import timed_log


COMMON_PROXY_URLS = [
    "http://127.0.0.1:7890",
    "http://127.0.0.1:7897",
    "http://127.0.0.1:1080",
    "http://127.0.0.1:1087",
    "http://127.0.0.1:8080",
]


def clean_text(value: str) -> str:
    return " ".join(html.unescape(value or "").split())


def child_text(item: ET.Element, names: list[str]) -> str:
    for name in names:
        node = item.find(name)
        if node is not None and node.text:
            return clean_text(node.text)
    for child in item:
        tag = child.tag.split("}")[-1].lower()
        if tag in names and child.text:
            return clean_text(child.text)
    return ""


def parse_rss_items(xml_text: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    rows = []
    for item in items:
        title = child_text(item, ["title"])
        summary = child_text(item, ["description", "summary", "content"])
        published_time = child_text(item, ["pubDate", "published", "updated"])
        url = child_text(item, ["link"])
        if not url:
            for child in item:
                tag = child.tag.split("}")[-1].lower()
                if tag == "link":
                    url = child.attrib.get("href", "")
                    break
        if not title and not url:
            continue
        rows.append(
            {
                "title": title,
                "summary": summary,
                "published_time": published_time,
                "url": url,
            }
        )
    return rows


def public_rss_sources(sources: pd.DataFrame) -> pd.DataFrame:
    if sources.empty:
        return sources
    return sources[
        sources["enabled"].eq(True)
        & sources["access_type"].astype(str).eq("public_rss")
        & sources["feed_type"].astype(str).eq("rss")
        & sources["requires_auth"].eq(False)
        & sources["url"].astype(str).str.strip().ne("")
    ].copy()


def proxy_is_open(proxy_url: str) -> bool:
    try:
        host_port = proxy_url.replace("http://", "").replace("https://", "")
        host, port = host_port.split(":", 1)
        with socket.create_connection((host, int(port)), timeout=0.5):
            return True
    except Exception:
        return False


def candidate_proxies() -> list[str]:
    proxies = []
    for key in ["NEWS_HTTP_PROXY", "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY"]:
        value = os.environ.get(key)
        if value:
            proxies.append(value)
    proxies.extend(COMMON_PROXY_URLS)
    return list(dict.fromkeys(proxies))


def curl_fetch(url: str, proxy_url: Optional[str] = None) -> str:
    command = ["curl", "-L", "--max-time", "20", "-A", "ai-industry-dashboard/1.0 research tool"]
    if proxy_url:
        command.extend(["--proxy", proxy_url])
    command.append(url)
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout


def fetch_url_text(url: str) -> str:
    errors = []
    try:
        response = requests.get(
            url,
            timeout=12,
            headers={"User-Agent": "ai-industry-dashboard/1.0 research tool"},
        )
        response.raise_for_status()
        return response.text
    except Exception as error:
        errors.append(f"requests direct: {error}")

    try:
        return curl_fetch(url)
    except Exception as error:
        errors.append(f"curl direct: {error}")

    for proxy_url in candidate_proxies():
        if not proxy_is_open(proxy_url):
            continue
        try:
            return curl_fetch(url, proxy_url)
        except Exception as error:
            errors.append(f"curl proxy {proxy_url}: {error}")

    raise RuntimeError("；".join(errors))


@timed_log
def fetch_public_rss_sources() -> dict:
    sources = public_rss_sources(load_unified_sources())
    existing = load_raw_news()
    existing_urls = set(existing["url"].dropna().astype(str)) if "url" in existing.columns else set()

    fetched_rows = []
    failed_sources = []
    fetched_count = 0
    duplicate_count = 0
    fetch_time = datetime.now(timezone.utc).isoformat()

    for _, source in sources.iterrows():
        source_name = str(source["source_name"])
        try:
            items = parse_rss_items(fetch_url_text(str(source["url"])))
            fetched_count += len(items)
            for item in items:
                url = item.get("url", "")
                if url and url in existing_urls:
                    duplicate_count += 1
                    continue
                mapping = map_news_keywords(item.get("title", ""), item.get("summary", ""))
                fetched_rows.append(
                    {
                        "fetch_time": fetch_time,
                        "published_time": item.get("published_time", ""),
                        "source_name": source_name,
                        "source_type": source.get("source_type", ""),
                        "access_type": source.get("access_type", ""),
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "url": url,
                        "raw_text": item.get("summary", ""),
                        "detected_keywords": mapping["detected_keywords"],
                        "detected_layer": mapping["detected_layer"],
                        "detected_category": mapping["detected_category"],
                        "event_type": mapping["event_type"],
                        "status": "pending_review",
                    }
                )
                if url:
                    existing_urls.add(url)
        except Exception as error:
            failed_sources.append(f"{source_name}: {error}")

    new_data = pd.DataFrame(fetched_rows, columns=REQUIRED_RAW_NEWS_COLUMNS)
    if existing.empty:
        combined = new_data
    else:
        combined = pd.concat([existing, new_data], ignore_index=True)
    if not combined.empty:
        combined = combined.drop_duplicates(subset=["url"], keep="first")
    save_raw_news(combined)

    return {
        "source_count": len(sources),
        "fetched_count": fetched_count,
        "new_count": len(new_data),
        "duplicate_count": duplicate_count,
        "failed_sources": failed_sources,
    }
