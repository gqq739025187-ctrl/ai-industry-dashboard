from datetime import datetime
from functools import wraps
import importlib
import time

import pandas as pd
import streamlit as st

import data_layer
import dashboard.views as views
from dashboard.logic import build_industry_chain_view

views = importlib.reload(views)


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


def remember_market_data(key: str, data: pd.DataFrame) -> pd.DataFrame:
    st.session_state[key] = data
    st.session_state[f"{key}_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return data


def cached_market_data(key: str) -> pd.DataFrame:
    return st.session_state.get(key, pd.DataFrame())


def cached_market_time(*keys: str) -> str:
    times = [st.session_state.get(f"{key}_time") for key in keys if st.session_state.get(f"{key}_time")]
    if not times:
        return "暂无行情缓存"
    return "最近缓存时间：" + " / ".join(times)


def cache_time_label(key: str) -> str:
    return st.session_state.get(f"{key}_time", "暂无缓存")


def render_cache_status() -> None:
    st.caption(
        "缓存状态："
        f"A股 {cache_time_label('a_share_market_data')} ｜ "
        f"美股 {cache_time_label('us_market_data')} ｜ "
        f"ETF {cache_time_label('etf_premium_data')} ｜ "
        f"均线 {cache_time_label('a_share_ma_data')}"
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

st.set_page_config(
    page_title="AI产业链投资驾驶舱",
    page_icon="📊",
    layout="wide",
)

st.title("AI产业链投资驾驶舱")
st.caption(f"本地研究平台 · 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

page = st.sidebar.radio(
    "页面",
    ["产业链首页", "AI产业链地图", "投资地图", "产业链百科", "事件中心", "资产数据库", "配置检查", "行情监控", "ETF监控", "AI日报"],
)

if st.sidebar.button("刷新行情缓存"):
    st.cache_data.clear()
    for key in [
        "a_share_market_data",
        "us_market_data",
        "a_share_ma_data",
        "etf_premium_data",
        "a_share_market_data_time",
        "us_market_data_time",
        "a_share_ma_data_time",
        "etf_premium_data_time",
    ]:
        st.session_state.pop(key, None)
    st.rerun()

st.sidebar.caption("目标速度：产业链首页/资产数据库 1 秒内；行情/ETF 3-8 秒；AI日报优先使用缓存。")

watchlist = load_watchlist_data()
a_share_watchlist = watchlist[watchlist["market"].eq("A股")]
us_watchlist = watchlist[watchlist["market"].eq("美股")]
etf_config = load_etf_config_data()
events = load_events_data()
a_share_tickers = tuple(a_share_watchlist["ticker"].astype(str).tolist())
us_tickers = tuple(us_watchlist["ticker"].astype(str).tolist())
etf_tickers = tuple(etf_config["ticker"].astype(str).tolist())

render_cache_status()

if page == "产业链首页":
    industry_chain_data = build_industry_chain_view(watchlist)
    dashboard_data = pd.DataFrame()
    us_dashboard_data = pd.DataFrame()
    if st.button("刷新产业链行情评分"):
        with st.spinner("正在刷新产业链行情评分..."):
            dashboard_data = remember_market_data("a_share_market_data", load_a_share_market_data(a_share_tickers))
            us_dashboard_data = remember_market_data("us_market_data", load_us_market_data(us_tickers))
            industry_chain_data = build_industry_chain_view(watchlist, dashboard_data, us_dashboard_data)
    views.render_industry_home(industry_chain_data, watchlist, dashboard_data, us_dashboard_data)
elif page == "AI产业链地图":
    views.render_ai_industry_chain_map(watchlist, events)
elif page == "投资地图":
    views.render_investment_map(watchlist, events)
elif page == "产业链百科":
    views.render_industry_wiki(watchlist)
elif page == "事件中心":
    views.render_event_center(events, watchlist)
elif page == "资产数据库":
    views.render_asset_database(watchlist)
elif page == "配置检查":
    views.render_config_check(watchlist, etf_config)
elif page == "行情监控":
    dashboard_data = cached_market_data("a_share_market_data")
    us_dashboard_data = cached_market_data("us_market_data")

    col1, col2, col3 = st.columns(3)
    if col1.button("刷新A股行情"):
        with st.spinner("正在刷新A股行情..."):
            dashboard_data = remember_market_data("a_share_market_data", load_a_share_market_data(a_share_tickers))
        st.rerun()
    if col2.button("刷新美股行情"):
        with st.spinner("正在刷新美股行情..."):
            us_dashboard_data = remember_market_data("us_market_data", load_us_market_data(us_tickers))
        st.rerun()
    if col3.button("刷新ETF数据"):
        with st.spinner("正在刷新ETF数据..."):
            remember_market_data("etf_premium_data", load_etf_premium_data(etf_tickers))
        st.rerun()

    cached_ma_data = cached_market_data("a_share_ma_data")
    if not dashboard_data.empty and not cached_ma_data.empty:
        dashboard_data = merge_a_share_ma_data(dashboard_data, cached_ma_data)
    if st.button("刷新均线数据"):
        with st.spinner("正在刷新A股均线数据..."):
            ma_data = remember_market_data("a_share_ma_data", load_a_share_ma_data(a_share_tickers))
            if not dashboard_data.empty:
                dashboard_data = remember_market_data("a_share_market_data", merge_a_share_ma_data(dashboard_data, ma_data))
        st.rerun()
    views.render_market_monitor(dashboard_data, us_dashboard_data, a_share_watchlist, data_layer)
elif page == "ETF监控":
    etf_premium_data = cached_market_data("etf_premium_data")
    if st.button("刷新ETF溢价数据"):
        with st.spinner("正在刷新ETF溢价数据..."):
            etf_premium_data = remember_market_data("etf_premium_data", load_etf_premium_data(etf_tickers))
        st.rerun()
    views.render_etf_monitor(etf_premium_data)
elif page == "AI日报":
    st.caption(cached_market_time("a_share_market_data", "us_market_data", "etf_premium_data"))
    dashboard_data = cached_market_data("a_share_market_data")
    us_dashboard_data = cached_market_data("us_market_data")
    etf_premium_data = cached_market_data("etf_premium_data")
    industry_chain_data = build_industry_chain_view(watchlist, dashboard_data, us_dashboard_data)
    views.render_daily_report(watchlist, events, dashboard_data, us_dashboard_data, etf_premium_data, industry_chain_data)

views.render_next_steps()
