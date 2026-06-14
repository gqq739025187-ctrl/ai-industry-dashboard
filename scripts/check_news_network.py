from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from data_sources.news_fetcher import candidate_proxies, curl_fetch, proxy_is_open  # noqa: E402


TEST_URL = "https://www.federalreserve.gov/feeds/press_all.xml"


def test_direct() -> bool:
    print("1. 测试直连 RSS...")
    try:
        text = curl_fetch(TEST_URL)
        print(f"✅ 直连成功，返回 {len(text)} 字符")
        return True
    except Exception as error:
        print(f"❌ 直连失败：{error}")
        return False


def test_proxies() -> bool:
    print("\n2. 测试本机代理端口...")
    success = False
    for proxy_url in candidate_proxies():
        if not proxy_is_open(proxy_url):
            print(f"⚪ 未发现可用端口：{proxy_url}")
            continue
        print(f"发现可用端口：{proxy_url}，正在测试 RSS...")
        try:
            text = curl_fetch(TEST_URL, proxy_url)
            print(f"✅ 代理成功：{proxy_url}，返回 {len(text)} 字符")
            success = True
        except Exception as error:
            print(f"❌ 代理失败：{proxy_url}，{error}")
    return success


def main() -> int:
    direct_ok = test_direct()
    proxy_ok = test_proxies()
    print("\n诊断结论：")
    if direct_ok or proxy_ok:
        print("网络通道可用，可以运行 python scripts/fetch_news.py")
        return 0
    print("当前终端无法访问公开 RSS。若浏览器可打开，通常是浏览器插件代理没有给终端使用。")
    print("可以设置环境变量 NEWS_HTTP_PROXY，例如：export NEWS_HTTP_PROXY=http://127.0.0.1:7890")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
