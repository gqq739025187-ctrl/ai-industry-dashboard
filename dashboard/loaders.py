from datetime import datetime
from functools import wraps
import time

import pandas as pd
import streamlit as st

import data_layer


def log_timing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        start_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[耗时日志] {func.__name__} 开始: {start_text}")
        try:
            return func(*args, **kwargs)
        finally:
            end = time.time()
            end_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[耗时日志] {func.__name__} 结束: {end_text}; 耗时: {end - start:.2f}秒")

    return wrapper


def empty_a_share_market_data(watchlist, error: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ticker": row["ticker"],
                "latest_price": None,
                "change_pct": None,
                "turnover": None,
                "ma20": None,
                "ma60": None,
                "status": f"A股行情获取失败: {error}",
            }
            for _, row in watchlist.iterrows()
        ]
    )


def empty_a_share_ma_data(watchlist, error: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ticker": row["ticker"],
                "ma20": None,
                "ma60": None,
                "ma_status": f"均线获取失败: {error}",
            }
            for _, row in watchlist.iterrows()
        ]
    )


def empty_us_market_data(watchlist, error: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ticker": row["ticker"],
                "latest_price": None,
                "change_pct": None,
                "volume": None,
                "turnover": None,
                "status": f"美股行情获取失败: {error}",
            }
            for _, row in watchlist.iterrows()
        ]
    )


def empty_etf_premium_data(etf_config, error: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "name": row["name"],
                "ticker": row["ticker"],
                "latest_price": None,
                "iopv": None,
                "nav": None,
                "valuation_source": "未获取",
                "premium_rate": None,
                "risk": "待确认",
                "status": f"ETF数据获取失败: {error}",
            }
            for _, row in etf_config.iterrows()
        ]
    )


def merge_a_share_ma_data(market_data: pd.DataFrame, ma_data: pd.DataFrame) -> pd.DataFrame:
    if ma_data is None or ma_data.empty:
        return market_data

    merged = market_data.drop(columns=["ma20", "ma60"], errors="ignore").merge(
        ma_data[["ticker", "ma20", "ma60", "ma_status"]],
        on="ticker",
        how="left",
    )
    if "status" in merged.columns:
        merged["status"] = merged.apply(
            lambda row: row["status"]
            if pd.isna(row.get("ma_status")) or row.get("ma_status") == "正常"
            else f"{row['status']}；{row['ma_status']}",
            axis=1,
        )
    return merged.drop(columns=["ma_status"], errors="ignore")


@st.cache_data(ttl=300, show_spinner=False)
@log_timing
def load_watchlist_data():
    return data_layer.load_watchlist()


@st.cache_data(ttl=300, show_spinner=False)
@log_timing
def load_etf_config_data():
    return data_layer.load_etf_config()


@st.cache_data(ttl=300, show_spinner=False)
@log_timing
def load_events_data():
    return data_layer.load_events()


@st.cache_data(ttl=300, show_spinner=False)
@log_timing
def load_event_impact_matrix_data():
    return data_layer.load_event_impact_matrix()


@st.cache_data(ttl=300, show_spinner=False)
@log_timing
def load_drivers_data():
    return data_layer.load_drivers()


@st.cache_data(ttl=300, show_spinner=False)
@log_timing
def load_chain_relations_data():
    return data_layer.load_chain_relations()


@st.cache_data(ttl=300, show_spinner=False)
@log_timing
def load_market_expectation_data():
    return data_layer.load_market_expectation()


@st.cache_data(ttl=300, show_spinner=False)
@log_timing
def load_raw_news_data():
    return data_layer.load_raw_news()


@st.cache_data(ttl=300, show_spinner=False)
@log_timing
def load_a_share_market_data(tickers):
    watchlist = data_layer.load_watchlist()
    a_share_watchlist = watchlist[watchlist["market"].eq("A股") & watchlist["ticker"].isin(tickers)]
    try:
        market_data = data_layer.fetch_market_data(a_share_watchlist.to_dict("records"))
    except Exception as error:
        market_data = empty_a_share_market_data(a_share_watchlist, str(error))
    return a_share_watchlist.merge(market_data, on="ticker", how="left")


@st.cache_data(ttl=300, show_spinner=False)
@log_timing
def load_a_share_ma_data(tickers):
    watchlist = data_layer.load_watchlist()
    a_share_watchlist = watchlist[watchlist["market"].eq("A股") & watchlist["ticker"].isin(tickers)]
    try:
        return data_layer.fetch_a_share_ma_data(a_share_watchlist.to_dict("records"))
    except Exception as error:
        return empty_a_share_ma_data(a_share_watchlist, str(error))


@st.cache_data(ttl=300, show_spinner=False)
@log_timing
def load_us_market_data(tickers):
    watchlist = data_layer.load_watchlist()
    us_watchlist = watchlist[watchlist["market"].eq("美股") & watchlist["ticker"].isin(tickers)]
    try:
        us_market_data = data_layer.fetch_us_market_data(us_watchlist.to_dict("records"))
    except Exception as error:
        us_market_data = empty_us_market_data(us_watchlist, str(error))
    return us_watchlist.merge(us_market_data, on="ticker", how="left")


@st.cache_data(ttl=600, show_spinner=False)
@log_timing
def load_etf_premium_data(tickers):
    etf_config = data_layer.load_etf_config()
    selected_config = etf_config[etf_config["ticker"].astype(str).isin([str(ticker) for ticker in tickers])]
    try:
        return data_layer.fetch_etf_premium_data(selected_config.to_dict("records"))
    except Exception as error:
        return empty_etf_premium_data(selected_config, str(error))
