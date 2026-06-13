from typing import Optional

import pandas as pd
import streamlit as st


def affected_company_names(watchlist: pd.DataFrame, category: str) -> str:
    companies = watchlist[watchlist["category"].astype(str).eq(str(category))]["name"].astype(str).tolist()
    return "、".join(companies) if companies else "暂无映射"


def render_event_impact_matrix(event_impact_matrix: pd.DataFrame, watchlist: pd.DataFrame) -> None:
    st.subheader("事件影响矩阵")
    st.caption("事件 -> 产业链 -> 公司。事件影响评分仅作为研究参考，不构成投资建议。")

    if event_impact_matrix is None or event_impact_matrix.empty:
        st.info("暂无事件影响矩阵配置。")
        return

    matrix = event_impact_matrix.copy()
    matrix["strength"] = pd.to_numeric(matrix["strength"], errors="coerce")
    event_names = sorted(matrix["event"].dropna().astype(str).unique())
    selected_event = st.selectbox("选择事件", event_names)
    selected_matrix = matrix[matrix["event"].astype(str).eq(selected_event)].copy()

    event_score = selected_matrix["strength"].sum(min_count=1)
    st.metric("事件影响评分", int(event_score) if pd.notna(event_score) else 0)
    st.caption("事件影响评分 = strength 求和，仅作为参考，不构成投资建议。")

    selected_matrix["受影响公司数量"] = selected_matrix["category"].apply(
        lambda category: int(watchlist["category"].astype(str).eq(str(category)).sum())
    )
    selected_matrix["对应公司"] = selected_matrix["category"].apply(lambda category: affected_company_names(watchlist, category))

    display = selected_matrix.rename(
        columns={
            "category": "受影响产业链",
            "direction": "影响方向",
            "strength": "影响强度",
            "time_horizon": "影响周期",
            "description": "影响说明",
        }
    )
    st.dataframe(
        display[["受影响产业链", "影响方向", "影响强度", "影响周期", "影响说明", "受影响公司数量", "对应公司"]],
        use_container_width=True,
        hide_index=True,
    )


def render_event_center(
    events: pd.DataFrame,
    watchlist: pd.DataFrame,
    event_impact_matrix: Optional[pd.DataFrame] = None,
) -> None:
    st.subheader("事件中心")
    st.caption("静态事件库：事件 -> 产业链 -> 公司。")

    industries = sorted(events["industry"].dropna().astype(str).unique())
    selected_industry = st.selectbox("按产业链筛选", ["全部"] + industries)
    filtered_events = events.copy()
    if selected_industry != "全部":
        filtered_events = filtered_events[filtered_events["industry"].eq(selected_industry)]

    display = filtered_events.rename(
        columns={
            "event_name": "事件名称",
            "industry": "对应产业链",
            "impact_level": "影响等级",
            "description": "事件说明",
        }
    )
    st.dataframe(
        display[["事件名称", "对应产业链", "影响等级", "事件说明"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("事件映射")
    for _, event in filtered_events.iterrows():
        affected = watchlist[watchlist["category"].eq(event["industry"])]
        with st.expander(f"{event['event_name']} -> {event['industry']}", expanded=False):
            st.write(f"事件说明：{event['description']}")
            st.write(f"影响等级：{event['impact_level']}")
            if affected.empty:
                st.info("当前股票池没有映射到该产业链的公司。")
                continue
            st.dataframe(
                affected[["name", "ticker", "market", "business", "market_focus", "description"]].rename(
                    columns={
                        "name": "公司名称",
                        "ticker": "股票代码",
                        "market": "市场",
                        "business": "主营业务",
                        "market_focus": "市场关注",
                        "description": "一句话理解",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    render_event_impact_matrix(event_impact_matrix if event_impact_matrix is not None else pd.DataFrame(), watchlist)
