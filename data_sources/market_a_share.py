import json
import re
import random
import socket
import subprocess
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlencode, urlsplit

import pandas as pd
import requests

from .utils import timed_log

MARKET_CACHE_FILE = "work/market_cache.json"
LOCAL_HISTORY_DIR = Path("data/history")
EASTMONEY_REALTIME_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"
EASTMONEY_KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
TENCENT_REALTIME_URL = "https://qt.gtimg.cn/q="
TENCENT_KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
SINA_KLINE_URL = "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"
FALLBACK_DNS_SERVERS = ("223.5.5.5", "119.29.29.29", "8.8.8.8", "1.1.1.1")


@timed_log
def http_get_text(url: str, params: Optional[dict] = None, timeout: int = 3, encoding: str = "utf-8") -> str:
    if params:
        url = f"{url}?{urlencode(params)}"

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        response.encoding = encoding
        return response.text
    except Exception as request_error:
        try:
            result = subprocess.run(
                ["curl", "-L", "--silent", "--show-error", "--max-time", str(timeout), url],
                check=True,
                capture_output=True,
            )
            return result.stdout.decode(encoding, errors="replace")
        except Exception as curl_error:
            try:
                return curl_with_fallback_dns(url, timeout, encoding)
            except Exception as fallback_error:
                raise RuntimeError(
                    f"requests失败: {request_error}; curl失败: {curl_error}; 备用DNS失败: {fallback_error}"
                ) from fallback_error


def curl_with_fallback_dns(url: str, timeout: int, encoding: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("备用DNS仅支持 HTTPS URL")

    ips = resolve_ipv4_with_public_dns(parsed.hostname, timeout)
    if not ips:
        raise ValueError(f"无法解析 {parsed.hostname}")

    last_error = None
    for ip in ips[:3]:
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-L",
                    "--silent",
                    "--show-error",
                    "--max-time",
                    str(timeout),
                    "--resolve",
                    f"{parsed.hostname}:443:{ip}",
                    url,
                ],
                check=True,
                capture_output=True,
            )
            return result.stdout.decode(encoding, errors="replace")
        except Exception as error:
            last_error = error

    raise RuntimeError(last_error)


def resolve_ipv4_with_public_dns(hostname: str, timeout: int) -> list[str]:
    query_id = random.randint(0, 65535)
    query = build_dns_query(hostname, query_id)
    ips = []

    for server in FALLBACK_DNS_SERVERS:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(timeout)
                sock.sendto(query, (server, 53))
                response, _ = sock.recvfrom(512)
            ips.extend(parse_dns_a_records(response, query_id))
        except Exception:
            continue

    return list(dict.fromkeys(ips))


def build_dns_query(hostname: str, query_id: int) -> bytes:
    header = query_id.to_bytes(2, "big") + b"\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
    question = b"".join(
        len(part).to_bytes(1, "big") + part.encode("ascii")
        for part in hostname.rstrip(".").split(".")
    )
    return header + question + b"\x00\x00\x01\x00\x01"


def parse_dns_a_records(response: bytes, query_id: int) -> list[str]:
    if len(response) < 12 or int.from_bytes(response[:2], "big") != query_id:
        return []

    question_count = int.from_bytes(response[4:6], "big")
    answer_count = int.from_bytes(response[6:8], "big")
    offset = 12

    for _ in range(question_count):
        offset = skip_dns_name(response, offset) + 4

    ips = []
    for _ in range(answer_count):
        offset = skip_dns_name(response, offset)
        if offset + 10 > len(response):
            break

        record_type = int.from_bytes(response[offset : offset + 2], "big")
        record_class = int.from_bytes(response[offset + 2 : offset + 4], "big")
        data_length = int.from_bytes(response[offset + 8 : offset + 10], "big")
        offset += 10

        if record_type == 1 and record_class == 1 and data_length == 4 and offset + 4 <= len(response):
            ips.append(".".join(str(part) for part in response[offset : offset + 4]))

        offset += data_length

    return ips


def skip_dns_name(packet: bytes, offset: int) -> int:
    while offset < len(packet):
        length = packet[offset]
        if length & 0xC0 == 0xC0:
            return offset + 2
        if length == 0:
            return offset + 1
        offset += length + 1

    return offset


def normalize_a_share_code(ticker: str) -> str:
    return ticker.split(".")[0]


def eastmoney_market_id(ticker: str) -> str:
    code = normalize_a_share_code(ticker)
    if ticker.endswith(".SH") or code.startswith(("5", "6", "9")):
        return "1"
    return "0"


def eastmoney_secid(ticker: str) -> str:
    return f"{eastmoney_market_id(ticker)}.{normalize_a_share_code(ticker)}"


def tencent_symbol(ticker: str) -> str:
    code = normalize_a_share_code(ticker)
    prefix = "sh" if ticker.endswith(".SH") or code.startswith(("5", "6", "9")) else "sz"
    return f"{prefix}{code}"


def load_market_cache() -> dict:
    try:
        with open(MARKET_CACHE_FILE, "r", encoding="utf-8") as cache_file:
            return json.load(cache_file)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def save_market_cache(rows: List[dict]) -> None:
    cache = load_market_cache()
    for row in rows:
        ticker = row.get("ticker")
        if not ticker:
            continue
        if row.get("latest_price") is None:
            continue
        cache[ticker] = row

    with open(MARKET_CACHE_FILE, "w", encoding="utf-8") as cache_file:
        json.dump(cache, cache_file, ensure_ascii=False, indent=2)


@timed_log
def fetch_market_data(watchlist_records: List[dict]) -> pd.DataFrame:
    print("[外部接口] A股实时行情 开始")
    rows = []
    cache = load_market_cache()
    realtime_quotes = fetch_a_share_realtime_quotes(watchlist_records)

    for record in watchlist_records:
        ticker = record["ticker"]
        market = record["market"]

        if market == "A股":
            rows.append(apply_cached_quote(fetch_a_share_realtime_data(ticker, realtime_quotes.get(ticker)), cache))
            continue

        rows.append(
            {
                "ticker": ticker,
                "latest_price": None,
                "change_pct": None,
                "turnover": None,
                "ma20": None,
                "ma60": None,
                "status": "本阶段仅接入A股",
            }
        )

    save_market_cache(rows)
    return pd.DataFrame(rows)


@timed_log
def fetch_a_share_ma_data(watchlist_records: List[dict]) -> pd.DataFrame:
    print("[外部接口] A股均线 开始")
    rows = []
    for record in watchlist_records:
        if record["market"] != "A股":
            continue
        rows.append(fetch_a_share_ma_for_ticker(record["ticker"]))
    return pd.DataFrame(rows)


def apply_cached_quote(row: dict, cache: dict) -> dict:
    if row.get("latest_price") is not None:
        return row

    cached_row = cache.get(row["ticker"])
    if not cached_row:
        return row

    original_status = row.get("status", "")
    cached = {
        "ticker": row["ticker"],
        "latest_price": cached_row.get("latest_price"),
        "change_pct": cached_row.get("change_pct"),
        "turnover": cached_row.get("turnover"),
        "ma20": None,
        "ma60": None,
    }
    cached["status"] = f"使用本地缓存；最新错误: {original_status}"
    return cached


@timed_log
def fetch_a_share_realtime_quotes(watchlist_records: List[dict]) -> dict:
    a_share_records = [record for record in watchlist_records if record["market"] == "A股"]
    if not a_share_records:
        return {}

    eastmoney_quotes = fetch_a_share_realtime_quotes_from_eastmoney(a_share_records)
    if eastmoney_quotes and not all(quote.get("error") for quote in eastmoney_quotes.values()):
        return eastmoney_quotes

    tencent_quotes = fetch_a_share_realtime_quotes_from_tencent(a_share_records)
    if tencent_quotes:
        return tencent_quotes

    return eastmoney_quotes


@timed_log
def fetch_a_share_realtime_quotes_from_eastmoney(a_share_records: List[dict]) -> dict:
    secids = ",".join(eastmoney_secid(record["ticker"]) for record in a_share_records)
    params = {
        "fltt": "2",
        "secids": secids,
        "fields": "f12,f14,f2,f3,f6",
    }

    try:
        payload = json.loads(http_get_text(EASTMONEY_REALTIME_URL, params=params))
        diff = payload.get("data", {}).get("diff") or []
    except Exception as error:
        return {
            record["ticker"]: {"error": f"实时行情获取失败: {error}"}
            for record in a_share_records
        }

    quotes = {}
    ticker_by_code = {normalize_a_share_code(record["ticker"]): record["ticker"] for record in a_share_records}
    for item in diff:
        ticker = ticker_by_code.get(str(item.get("f12")))
        if ticker:
            quotes[ticker] = {
                "latest_price": item.get("f2"),
                "change_pct": item.get("f3"),
                "turnover": item.get("f6"),
            }

    for record in a_share_records:
        quotes.setdefault(record["ticker"], {"error": "实时行情返回为空"})

    return quotes


@timed_log
def fetch_a_share_realtime_quotes_from_tencent(a_share_records: List[dict]) -> dict:
    symbol_to_ticker = {tencent_symbol(record["ticker"]): record["ticker"] for record in a_share_records}
    url = TENCENT_REALTIME_URL + ",".join(symbol_to_ticker.keys())

    try:
        text = http_get_text(url, encoding="gbk")
    except Exception as error:
        return {
            record["ticker"]: {"error": f"腾讯实时行情获取失败: {error}"}
            for record in a_share_records
        }

    quotes = {}
    for match in re.finditer(r'v_(?P<symbol>\w+)="(?P<body>[^"]*)";', text):
        symbol = match.group("symbol")
        ticker = symbol_to_ticker.get(symbol)
        if not ticker:
            continue

        fields = match.group("body").split("~")
        try:
            quotes[ticker] = {
                "latest_price": float(fields[3]),
                "change_pct": float(fields[32]),
                "turnover": float(fields[37]) * 10000,
            }
        except (IndexError, TypeError, ValueError) as error:
            quotes[ticker] = {"error": f"腾讯实时行情解析失败: {error}"}

    for record in a_share_records:
        quotes.setdefault(record["ticker"], {"error": "腾讯实时行情返回为空"})

    return quotes


@timed_log
def fetch_a_share_realtime_data(ticker: str, realtime_quote: Optional[dict]) -> dict:
    errors = []
    if realtime_quote and realtime_quote.get("error") and realtime_quote.get("latest_price") is None:
        errors.append(realtime_quote["error"])

    status = "正常" if not errors else "；".join(errors)
    return {
        "ticker": ticker,
        "latest_price": realtime_quote.get("latest_price") if realtime_quote else None,
        "change_pct": realtime_quote.get("change_pct") if realtime_quote else None,
        "turnover": realtime_quote.get("turnover") if realtime_quote else None,
        "ma20": None,
        "ma60": None,
        "status": status,
    }


@timed_log
def fetch_a_share_ma_for_ticker(ticker: str) -> dict:
    history, history_error = fetch_a_share_history(ticker)
    if history is None:
        return {
            "ticker": ticker,
            "ma20": None,
            "ma60": None,
            "ma_status": history_error,
        }

    return {
        "ticker": ticker,
        "ma20": history["close"].tail(20).mean(),
        "ma60": history["close"].tail(60).mean(),
        "ma_status": "正常",
    }


@timed_log
def fetch_a_share_data(ticker: str, realtime_quote: Optional[dict]) -> dict:
    errors = []
    if realtime_quote and realtime_quote.get("error") and realtime_quote.get("latest_price") is None:
        errors.append(realtime_quote["error"])

    latest_price = realtime_quote.get("latest_price") if realtime_quote else None
    change_pct = realtime_quote.get("change_pct") if realtime_quote else None
    turnover = realtime_quote.get("turnover") if realtime_quote else None
    ma20 = None
    ma60 = None

    history, history_error = fetch_a_share_history(ticker)
    if history is None:
        errors.append(history_error)
    else:
        latest_row = history.iloc[-1]
        latest_price = latest_price if latest_price not in (None, "-") else latest_row["close"]
        change_pct = change_pct if change_pct not in (None, "-") else latest_row.get("change_pct")
        turnover = turnover if turnover not in (None, "-") else latest_row.get("amount")
        ma20 = history["close"].tail(20).mean()
        ma60 = history["close"].tail(60).mean()

    status = "正常" if not errors else "；".join(errors)
    return {
        "ticker": ticker,
        "latest_price": latest_price,
        "change_pct": change_pct,
        "turnover": turnover,
        "ma20": ma20,
        "ma60": ma60,
        "status": status,
    }


@timed_log
def fetch_a_share_history(ticker: str) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    akshare_history, akshare_error = fetch_a_share_history_from_akshare(ticker)
    if akshare_history is not None:
        return akshare_history, None

    tencent_history, tencent_error = fetch_a_share_history_from_tencent(ticker)
    if tencent_history is not None:
        return tencent_history, None

    sina_history, sina_error = fetch_a_share_history_from_sina(ticker)
    if sina_history is not None:
        return sina_history, None

    eastmoney_history, eastmoney_error = fetch_a_share_history_from_eastmoney(ticker)
    if eastmoney_history is not None:
        return eastmoney_history, None

    local_history, local_error = fetch_a_share_history_from_local_csv(ticker)
    if local_history is not None:
        local_history.attrs["source"] = "local_csv"
        return local_history, None

    return None, (
        f"AkShare获取失败: {akshare_error}；"
        f"腾讯日线获取失败: {tencent_error}；"
        f"新浪日线获取失败: {sina_error}；"
        f"东方财富日线获取失败: {eastmoney_error}；"
        f"本地历史数据不可用: {local_error}"
    )


@timed_log
def fetch_a_share_history_from_akshare(ticker: str) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    try:
        import akshare as ak
    except Exception as error:
        return None, f"AkShare未安装: {error}"

    try:
        history = ak.stock_zh_a_hist(
            symbol=normalize_a_share_code(ticker),
            period="daily",
            start_date="20200101",
            end_date="20500101",
            adjust="qfq",
        )
        if history.empty:
            raise ValueError("AkShare返回空数据")

        history = history.rename(
            columns={
                "日期": "date",
                "收盘": "close",
                "成交额": "amount",
                "涨跌幅": "change_pct",
            }
        )
        return normalize_history_frame(history), None
    except Exception as error:
        return None, str(error)


@timed_log
def fetch_a_share_history_from_tencent(ticker: str) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    symbol = tencent_symbol(ticker)
    params = {
        "param": f"{symbol},day,,,90,qfq",
    }

    try:
        payload = json.loads(http_get_text(TENCENT_KLINE_URL, params=params, timeout=8))
        stock_data = payload.get("data", {}).get(symbol, {})
        klines = stock_data.get("qfqday") or stock_data.get("day") or []

        if len(klines) < 60:
            raise ValueError(f"腾讯日线数据不足 60 条，当前 {len(klines)} 条")

        history = pd.DataFrame(
            [
                {
                    "date": item[0],
                    "close": item[2],
                }
                for item in klines
                if len(item) >= 3
            ]
        )
        return normalize_history_frame(history), None
    except Exception as error:
        return None, str(error)


@timed_log
def fetch_a_share_history_from_sina(ticker: str) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    params = {
        "symbol": tencent_symbol(ticker),
        "scale": "240",
        "ma": "no",
        "datalen": "90",
    }

    try:
        payload = json.loads(http_get_text(SINA_KLINE_URL, params=params, timeout=8))

        if len(payload) < 60:
            raise ValueError(f"新浪日线数据不足 60 条，当前 {len(payload)} 条")

        history = pd.DataFrame(
            [
                {
                    "date": item.get("day"),
                    "close": item.get("close"),
                }
                for item in payload
            ]
        )
        return normalize_history_frame(history), None
    except Exception as error:
        return None, str(error)


@timed_log
def fetch_a_share_history_from_eastmoney(ticker: str) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    try:
        params = {
            "secid": eastmoney_secid(ticker),
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "end": "20500101",
            "lmt": "80",
        }
        payload = json.loads(http_get_text(EASTMONEY_KLINE_URL, params=params))
        klines = payload.get("data", {}).get("klines") or []

        if len(klines) < 60:
            raise ValueError(f"日线数据不足 60 条，当前 {len(klines)} 条")

        history = pd.DataFrame(
            [line.split(",") for line in klines],
            columns=[
                "date",
                "open",
                "close",
                "high",
                "low",
                "volume",
                "amount",
                "amplitude",
                "change_pct",
                "change_amount",
                "turnover_rate",
            ],
        )
        return normalize_history_frame(history), None
    except Exception as error:
        return None, str(error)


@timed_log
def fetch_a_share_history_from_local_csv(ticker: str) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    path = LOCAL_HISTORY_DIR / f"{ticker}.csv"
    if not path.exists():
        return None, f"缺少 {path}"

    try:
        history = pd.read_csv(path)
        return normalize_history_frame(history), None
    except Exception as error:
        return None, str(error)


def local_history_status(watchlist_records: List[dict]) -> pd.DataFrame:
    rows = []
    for record in watchlist_records:
        if record["market"] != "A股":
            continue

        ticker = record["ticker"]
        path = LOCAL_HISTORY_DIR / f"{ticker}.csv"
        if not path.exists():
            rows.append(
                {
                    "名称": record["name"],
                    "代码": ticker,
                    "本地文件": "缺失",
                    "有效行数": 0,
                    "是否够算均线": "否",
                    "说明": f"需要 {path}",
                }
            )
            continue

        try:
            history = normalize_history_frame(pd.read_csv(path))
            rows.append(
                {
                    "名称": record["name"],
                    "代码": ticker,
                    "本地文件": "已找到",
                    "有效行数": len(history),
                    "是否够算均线": "是",
                    "说明": "可计算 20/60 日均线",
                }
            )
        except Exception as error:
            rows.append(
                {
                    "名称": record["name"],
                    "代码": ticker,
                    "本地文件": "不可用",
                    "有效行数": 0,
                    "是否够算均线": "否",
                    "说明": str(error),
                }
            )

    return pd.DataFrame(rows)


def normalize_history_frame(history: pd.DataFrame) -> pd.DataFrame:
    required_columns = {"date", "close"}
    missing_columns = required_columns - set(history.columns)
    if missing_columns:
        raise ValueError(f"历史数据缺少字段: {', '.join(sorted(missing_columns))}")

    history = history.copy()
    history["close"] = pd.to_numeric(history["close"], errors="coerce")
    if "amount" in history.columns:
        history["amount"] = pd.to_numeric(history["amount"], errors="coerce")
    if "change_pct" in history.columns:
        history["change_pct"] = pd.to_numeric(history["change_pct"], errors="coerce")

    history = history.dropna(subset=["close"]).sort_values("date")
    if len(history) < 60:
        raise ValueError(f"有效日线数据不足 60 条，当前 {len(history)} 条")

    return history
