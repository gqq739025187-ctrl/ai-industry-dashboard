import pandas as pd
import streamlit as st

from config.constants import CATEGORY_ORDER


TIER_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3}


def confidence_percent(value) -> int:
    confidence = pd.to_numeric(value, errors="coerce")
    if pd.isna(confidence):
        return 0
    return int(max(0, min(100, confidence)))


def render_industry_wiki(watchlist: pd.DataFrame) -> None:
    st.subheader("产业链百科")

    category_count = watchlist["category"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()
    a_share_count = int(watchlist["market"].eq("A股").sum())
    us_count = int(watchlist["market"].eq("美股").sum())
    korea_count = int(watchlist["market"].eq("韩股").sum())

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("总公司数", len(watchlist))
    col2.metric("产业链数量", category_count)
    col3.metric("A股数量", a_share_count)
    col4.metric("美股数量", us_count)
    col5.metric("韩股数量", korea_count)

    category_order = [category for category in CATEGORY_ORDER if category in set(watchlist["category"].dropna().astype(str))]
    extra_categories = [
        category
        for category in sorted(watchlist["category"].dropna().astype(str).unique())
        if category not in category_order
    ]

    for category in category_order + extra_categories:
        members = watchlist[watchlist["category"].eq(category)].copy()
        if "tier" in members.columns:
            members["_tier_order"] = members["tier"].astype(str).map(TIER_ORDER).fillna(99)
            members = members.sort_values(["_tier_order", "name"])
        with st.expander(f"{category}（{len(members)}家公司）", expanded=False):
            for _, row in members.iterrows():
                st.markdown(f"#### {row['name']}（{row.get('tier', '')}）")
                st.caption(f"{row['ticker']} · {row['market']}")
                st.write(f"tier：{row.get('tier', '')}")
                st.write(f"主营业务：{row['business']}")
                st.write(f"市场关注：{row['market_focus']}")
                st.write(f"核心客户：{row.get('core_customer', '')}")
                st.write(f"上游：{row.get('upstream', '')}")
                st.write(f"下游：{row.get('downstream', '')}")
                st.write(f"利好逻辑：{row.get('bull_case', '')}")
                st.write(f"风险逻辑：{row.get('bear_case', '')}")
                st.write(f"一句话理解：{row['description']}")
                confidence = confidence_percent(row.get("confidence"))
                st.write(f"理解程度：{confidence}%")
                st.progress(confidence)
                st.divider()
