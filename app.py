from datetime import datetime

import pandas as pd
import streamlit as st

import data_layer
import dashboard.views as views
from dashboard.cache import cached_market_data, cached_market_time, remember_market_data, render_cache_status
from dashboard.logic import build_industry_chain_view
from dashboard.loaders import (
    load_a_share_ma_data,
    load_a_share_market_data,
    load_chain_relations_data,
    load_drivers_data,
    load_etf_config_data,
    load_event_impact_matrix_data,
    load_etf_premium_data,
    load_events_data,
    load_market_expectation_data,
    load_raw_news_data,
    load_us_market_data,
    load_watchlist_data,
    merge_a_share_ma_data,
)

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
event_impact_matrix = load_event_impact_matrix_data()
chain_relations = load_chain_relations_data()
market_expectation = load_market_expectation_data()
drivers = load_drivers_data()
raw_news = load_raw_news_data()
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
    views.render_industry_home(
        industry_chain_data,
        watchlist,
        dashboard_data,
        us_dashboard_data,
        chain_relations,
        market_expectation,
        events,
        drivers,
    )
elif page == "AI产业链地图":
    views.render_ai_industry_chain_map(watchlist, events, chain_relations, market_expectation, drivers)
elif page == "投资地图":
    views.render_investment_map(watchlist, events)
elif page == "产业链百科":
    views.render_industry_wiki(watchlist)
elif page == "事件中心":
    views.render_event_center(events, watchlist, event_impact_matrix, raw_news)
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
