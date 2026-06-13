from typing import List, Optional

import pandas as pd

from .market_a_share import fetch_a_share_realtime_quotes, normalize_a_share_code
from .utils import parse_optional_float, timed_log


ETF_CONFIG_FILE = "etf_config.csv"
ETF_CONFIG_COLUMNS = ["name", "ticker", "manual_iopv", "manual_nav"]


@timed_log
def load_etf_config() -> pd.DataFrame:
    etf_config = pd.read_csv(ETF_CONFIG_FILE)
    for column in ETF_CONFIG_COLUMNS:
        if column not in etf_config.columns:
            etf_config[column] = ""
    return etf_config[ETF_CONFIG_COLUMNS]


@timed_log
def fetch_etf_premium_data(etf_records: List[dict]) -> pd.DataFrame:
    print("[外部接口] ETF数据 开始")
    rows = []
    realtime_quotes = fetch_a_share_realtime_quotes(
        [
            {
                "ticker": normalize_etf_ticker(record["ticker"]),
                "market": "A股",
            }
            for record in etf_records
        ]
    )
    auto_values = fetch_etf_auto_value_map()

    for record in etf_records:
        ticker = normalize_etf_ticker(record["ticker"])
        quote = realtime_quotes.get(ticker, {})
        latest_price = quote.get("latest_price")
        auto_value = auto_values.get(normalize_a_share_code(ticker), {})
        manual_iopv = parse_optional_float(record.get("manual_iopv"))
        manual_nav = parse_optional_float(record.get("manual_nav"))
        iopv = auto_value.get("iopv") or manual_iopv
        nav = auto_value.get("nav") or manual_nav
        valuation_base = iopv or nav
        valuation_source = "自动获取" if auto_value else "手动填写"
        errors = []

        if quote.get("error") and latest_price is None:
            errors.append(f"价格获取失败: {quote['error']}")
        if latest_price is None:
            errors.append("缺少ETF市场价格")
        if valuation_base is None:
            valuation_source = "未获取"
            errors.append("无法自动获取IOPV/净值，且配置文件未填写manual_iopv或manual_nav")

        premium_rate = None
        if latest_price is not None and valuation_base not in (None, 0):
            premium_rate = (float(latest_price) - float(valuation_base)) / float(valuation_base) * 100

        risk = "待确认"
        if premium_rate is not None:
            risk = "正常"
            if premium_rate > 10:
                risk = "高溢价风险"
            elif premium_rate > 5:
                risk = "关注"

        rows.append(
            {
                "name": record["name"],
                "ticker": ticker,
                "latest_price": latest_price,
                "iopv": iopv,
                "nav": nav,
                "valuation_source": valuation_source,
                "premium_rate": premium_rate,
                "risk": risk,
                "status": "正常" if not errors else "；".join(errors),
            }
        )

    return pd.DataFrame(rows)


def normalize_etf_ticker(ticker: str) -> str:
    code = str(ticker).strip()
    if "." in code:
        return code
    suffix = "SH" if code.startswith("5") else "SZ"
    return f"{code}.{suffix}"


@timed_log
def fetch_etf_auto_value_map() -> dict:
    try:
        import akshare as ak
    except Exception:
        return {}

    try:
        spot = ak.fund_etf_spot_em()
    except Exception:
        return {}

    if spot is None or spot.empty or "代码" not in spot.columns:
        return {}

    iopv_columns = ["IOPV实时估值", "IOPV"]
    nav_columns = [
        "IOPV实时估值",
        "IOPV",
        "基金净值",
        "单位净值",
        "最新净值",
        "净值",
    ]
    iopv_column = next((column for column in iopv_columns if column in spot.columns), None)
    nav_column = next((column for column in nav_columns if column in spot.columns), None)
    if iopv_column is None and nav_column is None:
        return {}

    result = {}
    for _, row in spot.iterrows():
        code = str(row.get("代码", "")).strip()
        iopv = parse_optional_float(row.get(iopv_column)) if iopv_column else None
        nav = parse_optional_float(row.get(nav_column)) if nav_column else None
        if code and (iopv is not None or nav is not None):
            result[code] = {"iopv": iopv, "nav": nav}

    return result
