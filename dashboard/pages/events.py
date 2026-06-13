import pandas as pd
import streamlit as st


def render_event_center(events: pd.DataFrame, watchlist: pd.DataFrame) -> None:
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
