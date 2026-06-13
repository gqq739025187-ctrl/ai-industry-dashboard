from datetime import datetime

import pandas as pd
import streamlit as st


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
