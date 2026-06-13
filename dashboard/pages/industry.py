from typing import Optional

import pandas as pd
import streamlit as st

from dashboard.logic import build_industry_chain_members, format_optional_number, format_turnover


def format_confidence(value) -> str:
    confidence = pd.to_numeric(value, errors="coerce")
    if pd.isna(confidence):
        return "未填写"
    return f"{int(confidence)}%"


def market_expectation_for_category(market_expectation: pd.DataFrame, category: str) -> pd.DataFrame:
    if market_expectation is None or market_expectation.empty or "category" not in market_expectation.columns:
        return pd.DataFrame()
    return market_expectation[market_expectation["category"].astype(str).eq(category)].copy()


def top_benefit_categories(market_expectation: pd.DataFrame, limit: int = 3) -> pd.DataFrame:
    if market_expectation is None or market_expectation.empty:
        return pd.DataFrame()

    data = market_expectation.copy()
    for column in ["logic_score", "cycle_score", "sentiment_score", "valuation_score"]:
        data[column] = pd.to_numeric(data.get(column), errors="coerce")
    data["受益分数"] = data["logic_score"].fillna(0) + data["cycle_score"].fillna(0)
    return data.sort_values("受益分数", ascending=False).head(limit)


def representative_names(watchlist: pd.DataFrame, category: str) -> str:
    members = watchlist[watchlist["category"].astype(str).eq(category)]
    if members.empty:
        return "未覆盖"
    return "、".join(members["name"].astype(str).head(4).tolist())


def expectation_status(row: pd.Series) -> str:
    logic_score = pd.to_numeric(row.get("logic_score"), errors="coerce")
    sentiment_score = pd.to_numeric(row.get("sentiment_score"), errors="coerce")
    valuation_score = pd.to_numeric(row.get("valuation_score"), errors="coerce")

    if pd.notna(sentiment_score) and pd.notna(valuation_score) and sentiment_score >= 80 and valuation_score <= 50:
        return "市场关注度高，估值吸引力偏低"
    if pd.notna(sentiment_score) and pd.notna(logic_score) and sentiment_score <= 65 and logic_score >= 80:
        return "逻辑较强，市场关注度相对低"
    return "市场预期相对均衡"


def render_core_questions(
    watchlist: pd.DataFrame,
    market_expectation: Optional[pd.DataFrame] = None,
    chain_relations: Optional[pd.DataFrame] = None,
    events: Optional[pd.DataFrame] = None,
    drivers: Optional[pd.DataFrame] = None,
) -> None:
    st.subheader("核心四问")

    st.markdown("#### 1. AI资本开支是否增强？")
    capex = market_expectation_for_category(market_expectation, "云厂Capex")
    if capex.empty:
        st.info("暂无云厂Capex预期配置")
    else:
        display = capex.rename(
            columns={
                "logic_score": "Logic Score",
                "cycle_score": "Cycle Score",
                "sentiment_score": "Sentiment Score",
                "expectation_level": "Expectation Level",
                "note": "Note",
            }
        )
        st.dataframe(
            display[["Logic Score", "Cycle Score", "Sentiment Score", "Expectation Level", "Note"]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("##### 云厂Capex核心驱动因素")
    capex_drivers = (
        drivers[drivers["category"].astype(str).eq("云厂Capex")].copy()
        if drivers is not None and not drivers.empty and "category" in drivers.columns
        else pd.DataFrame()
    )
    if capex_drivers.empty:
        st.info("暂无云厂Capex驱动因素配置")
    else:
        driver_display = capex_drivers.rename(
            columns={
                "driver": "驱动因素",
                "direction": "方向",
                "importance": "重要性",
                "leading_or_lagging": "领先/滞后",
                "description": "说明",
            }
        )
        st.dataframe(
            driver_display[["驱动因素", "方向", "重要性", "领先/滞后", "说明"]],
            use_container_width=True,
            hide_index=True,
        )

    top_categories = top_benefit_categories(market_expectation)

    st.markdown("#### 2. 哪个产业链环节最受益？")
    if top_categories.empty:
        st.info("暂无市场预期配置")
    else:
        benefit_display = top_categories.rename(
            columns={
                "category": "产业链环节",
                "logic_score": "Logic Score",
                "cycle_score": "Cycle Score",
                "note": "Note",
            }
        )
        st.dataframe(
            benefit_display[["产业链环节", "Logic Score", "Cycle Score", "Note"]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### 3. 当前股票池是否覆盖这些环节？")
    if top_categories.empty:
        st.info("暂无可检查的受益环节")
    else:
        coverage_rows = []
        for _, row in top_categories.iterrows():
            category = str(row["category"])
            members = watchlist[watchlist["category"].astype(str).eq(category)]
            coverage_rows.append(
                {
                    "产业链环节": category,
                    "覆盖公司数": len(members),
                    "代表公司": representative_names(watchlist, category),
                }
            )
        st.dataframe(pd.DataFrame(coverage_rows), use_container_width=True, hide_index=True)

    st.markdown("#### 4. 市场是否已经交易了这个逻辑？")
    if top_categories.empty:
        st.info("暂无市场预期配置")
    else:
        trade_rows = []
        for _, row in top_categories.iterrows():
            trade_rows.append(
                {
                    "产业链环节": row["category"],
                    "Sentiment Score": row["sentiment_score"],
                    "Valuation Score": row["valuation_score"],
                    "Expectation Level": row["expectation_level"],
                    "状态提示": expectation_status(row),
                }
            )
        st.dataframe(pd.DataFrame(trade_rows), use_container_width=True, hide_index=True)


def render_industry_home(
    industry_chain_data: pd.DataFrame,
    watchlist: pd.DataFrame,
    dashboard_data: Optional[pd.DataFrame] = None,
    us_dashboard_data: Optional[pd.DataFrame] = None,
    chain_relations: Optional[pd.DataFrame] = None,
    market_expectation: Optional[pd.DataFrame] = None,
    events: Optional[pd.DataFrame] = None,
    drivers: Optional[pd.DataFrame] = None,
) -> None:
    st.subheader("产业链首页")
    render_core_questions(watchlist, market_expectation, chain_relations, events, drivers)

    has_market_data = industry_chain_data["平均涨跌幅%"].notna().any() if "平均涨跌幅%" in industry_chain_data.columns else False
    if has_market_data:
        st.caption("已刷新行情：评分默认基于涨跌幅和上涨占比；如已刷新均线，则纳入20日/60日均线强度。")
    else:
        st.warning("未刷新行情。当前只显示静态产业链信息。")

    display = industry_chain_data.copy()
    if display.empty:
        st.dataframe(display, use_container_width=True, hide_index=True)
        return

    if has_market_data:
        display["平均涨跌幅%"] = display["平均涨跌幅%"].apply(format_optional_number)
        display["总成交额"] = display["总成交额"].apply(format_turnover)
        display["评分"] = display["评分"].apply(lambda value: "待评分" if pd.isna(value) else f"{int(value)}")
        display = display[
            [
                "产业链",
                "成员数量",
                "代表公司",
                "平均涨跌幅%",
                "上涨/下跌家数",
                "20日均线强度",
                "60日均线强度",
                "总成交额",
                "评分",
                "状态",
            ]
        ]
    else:
        display = display[
            [
                "产业链",
                "成员数量",
                "代表公司",
                "business",
                "market_focus",
                "状态",
            ]
        ]

    st.dataframe(display, use_container_width=True, hide_index=True)

    st.subheader("产业链明细")
    for chain_name in industry_chain_data["产业链"].astype(str).tolist():
        members = build_industry_chain_members(
            watchlist,
            chain_name,
            dashboard_data if dashboard_data is not None else pd.DataFrame(),
            us_dashboard_data if us_dashboard_data is not None else pd.DataFrame(),
        )
        with st.expander(chain_name, expanded=False):
            member_display = members.rename(
                columns={
                    "name": "公司名称",
                    "ticker": "股票代码",
                    "market": "市场",
                    "latest_price": "最新价",
                    "change_pct": "涨跌幅",
                    "ma20": "20日均线",
                    "ma60": "60日均线",
                }
            )
            if has_market_data:
                member_display["最新价"] = member_display["最新价"].apply(format_optional_number)
                member_display["涨跌幅"] = member_display["涨跌幅"].apply(format_optional_number)
                member_display["20日均线"] = member_display["20日均线"].apply(format_optional_number)
                member_display["60日均线"] = member_display["60日均线"].apply(format_optional_number)
                columns = [
                    "公司名称",
                    "股票代码",
                    "市场",
                    "最新价",
                    "涨跌幅",
                    "20日均线",
                    "60日均线",
                    "business",
                    "market_focus",
                    "description",
                ]
            else:
                columns = ["公司名称", "股票代码", "市场", "business", "market_focus", "description"]
            st.dataframe(member_display[columns], use_container_width=True, hide_index=True)


def render_asset_database(watchlist: pd.DataFrame) -> None:
    st.subheader("资产数据库")
    display = watchlist.rename(
        columns={
            "name": "名称",
            "ticker": "代码",
            "market": "市场",
            "theme": "主题",
            "category": "产业链",
            "tier": "层级",
            "business": "业务",
            "market_focus": "市场关注",
            "description": "一句话说明",
            "core_customer": "核心客户",
            "upstream": "上游",
            "downstream": "下游",
            "bull_case": "最大利好逻辑",
            "bear_case": "最大风险逻辑",
            "confidence": "理解程度",
        }
    )
    if "理解程度" in display.columns:
        display["理解程度"] = display["理解程度"].apply(format_confidence)
    st.dataframe(display, use_container_width=True, hide_index=True)
