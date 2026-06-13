from typing import Optional

import pandas as pd
import streamlit as st

from config.constants import CATEGORY_ORDER, CHAIN_ORDER


def render_investment_map(watchlist: pd.DataFrame, events: pd.DataFrame) -> None:
    st.subheader("投资地图")
    st.caption("AI产业链静态知识图谱：AI基础设施 -> 产业链环节 -> 公司 -> 业务 -> 关注点 -> 事件。")

    category_count = watchlist["category"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()
    col1, col2, col3 = st.columns(3)
    col1.metric("总公司数", len(watchlist))
    col2.metric("产业链数量", category_count)
    col3.metric("事件数量", len(events))

    event_map = {
        category: events[events["industry"].eq(category)].copy()
        for category in watchlist["category"].dropna().astype(str).unique()
    }
    category_order = [category for category in CATEGORY_ORDER if category in set(watchlist["category"].dropna().astype(str))]
    extra_categories = [
        category
        for category in sorted(watchlist["category"].dropna().astype(str).unique())
        if category not in category_order
    ]

    st.markdown("### AI基础设施")
    for category in category_order + extra_categories:
        members = watchlist[watchlist["category"].eq(category)].copy()
        related_events = event_map.get(category, pd.DataFrame())

        with st.expander(f"{category}（{len(members)}家公司）", expanded=False):
            st.markdown("**相关事件**")
            if related_events is None or related_events.empty:
                st.info("暂无相关事件")
            else:
                for _, event in related_events.iterrows():
                    st.write(f"- {event['event_name']}（影响等级：{event['impact_level']}） - {event['description']}")

            st.markdown("**对应公司**")
            for _, row in members.iterrows():
                st.markdown(f"#### {row['name']}")
                st.caption(f"{row['ticker']} · {row['market']}")
                st.write(f"主营业务：{row['business']}")
                st.write(f"市场关注：{row['market_focus']}")
                st.write(f"一句话理解：{row['description']}")

                company_events = related_events["event_name"].tolist() if related_events is not None and not related_events.empty else []
                if company_events:
                    st.write("相关事件：" + "、".join(company_events))
                else:
                    st.write("相关事件：暂无相关事件")
                st.divider()

    st.caption("本页面为静态产业链知识图谱，不构成投资建议。")


def relation_display(relations: pd.DataFrame) -> pd.DataFrame:
    return relations.rename(
        columns={
            "source_category": "上游来源",
            "target_category": "下游去向",
            "relation_type": "关系类型",
            "description": "关系说明",
            "importance": "重要性",
        }
    )


def expectation_display(expectation: pd.DataFrame) -> pd.DataFrame:
    return expectation.rename(
        columns={
            "logic_score": "Logic Score",
            "cycle_score": "Cycle Score",
            "sentiment_score": "Sentiment Score",
            "valuation_score": "Valuation Score",
            "expectation_level": "Expectation Level",
            "note": "Note",
        }
    )


def render_ai_industry_chain_map(
    watchlist: pd.DataFrame,
    events: pd.DataFrame,
    chain_relations: Optional[pd.DataFrame] = None,
    market_expectation: Optional[pd.DataFrame] = None,
) -> None:
    st.subheader("AI产业链地图")
    st.caption("本页面用于展示 AI基础设施产业链上下游关系，不展示实时行情。")

    event_map = {
        category: events[events["industry"].eq(category)].copy()
        for category in events["industry"].dropna().astype(str).unique()
    }
    relations = chain_relations.copy() if chain_relations is not None else pd.DataFrame()
    expectations = market_expectation.copy() if market_expectation is not None else pd.DataFrame()

    for index, category in enumerate(CHAIN_ORDER):
        members = watchlist[watchlist["category"].eq(category)].copy()
        related_events = event_map.get(category, pd.DataFrame())
        upstream_relations = relations[relations["target_category"].eq(category)] if not relations.empty else pd.DataFrame()
        downstream_relations = relations[relations["source_category"].eq(category)] if not relations.empty else pd.DataFrame()
        category_expectation = expectations[expectations["category"].eq(category)] if not expectations.empty else pd.DataFrame()
        representative = "、".join(members["name"].astype(str).head(3).tolist()) if not members.empty else "暂无"
        event_count = len(related_events) if related_events is not None else 0

        with st.expander(f"{category}（{len(members)}家公司）", expanded=False):
            overview = pd.DataFrame(
                [
                    {"项目": "环节名称", "内容": category},
                    {"项目": "公司数量", "内容": len(members)},
                    {"项目": "代表公司", "内容": representative},
                    {"项目": "相关事件数量", "内容": event_count},
                ]
            )
            st.dataframe(overview, use_container_width=True, hide_index=True)

            st.markdown("#### 市场预期")
            if category_expectation.empty:
                st.info("暂无市场预期配置")
            else:
                st.dataframe(
                    expectation_display(category_expectation)[
                        [
                            "Logic Score",
                            "Cycle Score",
                            "Sentiment Score",
                            "Valuation Score",
                            "Expectation Level",
                            "Note",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

            st.markdown("#### 产业链关系")
            related_relations = pd.concat([upstream_relations, downstream_relations], ignore_index=True, sort=False)
            if related_relations.empty:
                st.info("暂无产业链关系配置")
            else:
                st.dataframe(
                    relation_display(related_relations)[["上游来源", "下游去向", "关系类型", "关系说明", "重要性"]],
                    use_container_width=True,
                    hide_index=True,
                )

            st.markdown("#### 公司")
            if members.empty:
                st.info("暂无公司配置")
            else:
                for _, row in members.iterrows():
                    st.markdown(f"##### {row['name']}")
                    st.write(f"股票代码：{row['ticker']}")
                    st.write(f"市场：{row['market']}")
                    st.write(f"主营业务：{row['business']}")
                    st.write(f"市场关注：{row['market_focus']}")
                    st.write(f"一句话理解：{row['description']}")
                    st.divider()

            st.markdown("#### 相关事件")
            if related_events is None or related_events.empty:
                st.info("暂无相关事件")
            else:
                for _, event in related_events.iterrows():
                    st.write(f"- {event['event_name']}（影响等级：{event['impact_level']}） - {event['description']}")

        if index < len(CHAIN_ORDER) - 1:
            st.markdown("### ↓")

    st.caption("本页面为本地产业链知识图谱，不构成投资建议。")
