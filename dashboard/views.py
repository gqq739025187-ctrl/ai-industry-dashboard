import streamlit as st

from dashboard.pages.config_check import build_etf_issues, build_watchlist_issues, render_config_check
from dashboard.pages.daily_report import render_daily_report
from dashboard.pages.etf import render_etf_monitor
from dashboard.pages.events import render_event_center
from dashboard.pages.industry import render_asset_database, render_industry_home
from dashboard.pages.maps import render_ai_industry_chain_map, render_investment_map
from dashboard.pages.market import render_market_monitor
from dashboard.pages.wiki import render_industry_wiki


def render_next_steps() -> None:
    st.subheader("下一阶段")
    st.write("接下来进入 P1：美股联动、产业链百科，以及产业链首页的进一步增强。")


__all__ = [
    "build_etf_issues",
    "build_watchlist_issues",
    "render_ai_industry_chain_map",
    "render_asset_database",
    "render_config_check",
    "render_daily_report",
    "render_etf_monitor",
    "render_event_center",
    "render_industry_home",
    "render_industry_wiki",
    "render_investment_map",
    "render_market_monitor",
    "render_next_steps",
]
