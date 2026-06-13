import pandas as pd
import streamlit as st

from config.constants import CATEGORY_ORDER
from dashboard.logic import (
    build_daily_conclusion,
    build_daily_overview,
    build_event_focus,
    classify_market_state,
    format_optional_number,
    format_percent,
)


def render_daily_report(
    watchlist: pd.DataFrame,
    events: pd.DataFrame,
    dashboard_data: pd.DataFrame,
    us_dashboard_data: pd.DataFrame,
    etf_premium_data: pd.DataFrame,
    industry_chain_data: pd.DataFrame,
) -> None:
    st.subheader("AI产业链日报")
    has_market_data = (
        industry_chain_data is not None
        and not industry_chain_data.empty
        and "平均涨跌幅%" in industry_chain_data.columns
        and industry_chain_data["平均涨跌幅%"].notna().any()
    )

    if not has_market_data:
        st.warning("请先刷新行情缓存后生成日报。")
        st.caption("本日报基于本地规则生成，不构成投资建议。")
        return

    today_text = pd.Timestamp.today().strftime("%Y-%m-%d")
    overview = build_daily_overview(watchlist, industry_chain_data, dashboard_data, us_dashboard_data)
    conclusion = build_daily_conclusion(industry_chain_data, etf_premium_data)
    market_state, etf_warning = classify_market_state(industry_chain_data, etf_premium_data)

    high_risk_etfs = []
    if etf_premium_data is not None and not etf_premium_data.empty and "premium_rate" in etf_premium_data.columns:
        premium_data = etf_premium_data.copy()
        premium_data["premium_rate"] = pd.to_numeric(premium_data["premium_rate"], errors="coerce")
        high_risk_etfs = premium_data[premium_data["premium_rate"] >= 10]["name"].astype(str).tolist()

    st.markdown(f"### AI产业链日报")
    st.write(f"日期：{today_text}")

    st.markdown("#### 今日结论")
    st.info(conclusion)

    st.markdown("#### 重要信号")
    signal_rows = [
        {"信号": "市场状态", "内容": market_state},
        {"信号": "最强产业链", "内容": overview["最强产业链"]},
        {"信号": "最弱产业链", "内容": overview["最弱产业链"]},
        {"信号": "高风险ETF", "内容": "、".join(high_risk_etfs) if high_risk_etfs else "无"},
    ]
    if etf_warning:
        signal_rows.append({"信号": "ETF提示", "内容": etf_warning})
    st.dataframe(pd.DataFrame(signal_rows), use_container_width=True, hide_index=True)

    st.markdown("#### 今日总览")
    overview_display = pd.DataFrame(
        [
            {"指标": "股票池公司数量", "数值": overview["股票池公司数量"]},
            {"指标": "产业链数量", "数值": overview["产业链数量"]},
            {"指标": "今日上涨家数", "数值": overview["今日上涨家数"]},
            {"指标": "今日下跌家数", "数值": overview["今日下跌家数"]},
            {"指标": "平均涨跌幅", "数值": format_percent(overview["平均涨跌幅"])},
            {"指标": "最强产业链", "数值": overview["最强产业链"]},
            {"指标": "最弱产业链", "数值": overview["最弱产业链"]},
        ]
    )
    st.dataframe(overview_display, use_container_width=True, hide_index=True)

    st.markdown("#### 产业链状态")
    industry_display = industry_chain_data.copy()
    ordered_categories = [category for category in CATEGORY_ORDER if category in set(industry_display["产业链"].astype(str))]
    extra_categories = [
        category
        for category in industry_display["产业链"].astype(str).tolist()
        if category not in ordered_categories
    ]
    category_order = ordered_categories + extra_categories
    industry_display["_order"] = industry_display["产业链"].astype(str).apply(
        lambda value: category_order.index(value) if value in category_order else len(category_order)
    )
    industry_display = industry_display.sort_values("_order")
    industry_display["评分"] = industry_display["评分"].apply(lambda value: "待评分" if pd.isna(value) else int(value))
    industry_display["平均涨跌幅%"] = industry_display["平均涨跌幅%"].apply(format_percent)
    industry_display = industry_display.rename(
        columns={
            "产业链": "产业链",
            "状态": "状态",
            "平均涨跌幅%": "平均涨跌幅",
            "上涨/下跌家数": "上涨/下跌家数",
            "代表公司": "代表公司",
        }
    )
    st.dataframe(
        industry_display[["产业链", "评分", "状态", "平均涨跌幅", "上涨/下跌家数", "代表公司"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### ETF风险提示")
    if etf_premium_data is None or etf_premium_data.empty:
        st.info("ETF缓存暂无数据。请先进入“ETF监控”刷新。")
    else:
        etf_display = etf_premium_data.copy()
        etf_display["premium_rate"] = pd.to_numeric(etf_display["premium_rate"], errors="coerce")
        etf_display["净值/IOPV"] = etf_display["iopv"].where(etf_display["iopv"].notna(), etf_display["nav"])
        etf_display["风险状态"] = etf_display.apply(
            lambda row: "高溢价风险" if pd.notna(row["premium_rate"]) and row["premium_rate"] >= 10 else row.get("risk", "待确认"),
            axis=1,
        )
        etf_display = etf_display.rename(
            columns={
                "name": "ETF",
                "ticker": "代码",
                "latest_price": "ETF价格",
                "premium_rate": "溢价率",
            }
        )
        etf_display["ETF价格"] = etf_display["ETF价格"].apply(format_optional_number)
        etf_display["净值/IOPV"] = etf_display["净值/IOPV"].apply(format_optional_number)
        etf_display["溢价率"] = etf_display["溢价率"].apply(format_percent)
        st.dataframe(
            etf_display[["ETF", "代码", "ETF价格", "净值/IOPV", "溢价率", "风险状态"]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### 今日关注事件")
    focus_events = build_event_focus(events, watchlist)
    if focus_events.empty:
        st.info("暂无事件记录。")
    else:
        event_display = focus_events.rename(
            columns={
                "event_name": "事件名称",
                "industry": "对应产业链",
                "impact_level": "影响等级",
                "description": "事件说明",
            }
        )
        st.dataframe(
            event_display[["事件名称", "对应产业链", "影响等级", "事件说明", "受影响公司"]],
            use_container_width=True,
            hide_index=True,
        )

    st.caption("本日报基于本地规则生成，不构成投资建议。")
