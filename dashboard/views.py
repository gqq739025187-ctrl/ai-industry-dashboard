from typing import Optional

import pandas as pd
import streamlit as st

from dashboard.logic import (
    build_industry_chain_members,
    build_daily_conclusion,
    build_daily_overview,
    build_event_focus,
    classify_selloff,
    classify_market_state,
    format_optional_number,
    format_percent,
    format_turnover,
    format_volume,
    summarize_status,
)

REQUIRED_WATCHLIST_COLUMNS = [
    "name",
    "ticker",
    "market",
    "theme",
    "category",
    "business",
    "market_focus",
    "description",
]
REQUIRED_CATEGORIES = ["GPU", "HBM", "光模块", "光器件", "交换机/ASIC", "云厂Capex", "PCB"]
REQUIRED_ETF_TICKERS = ["513310.SH", "515880.SH", "513520.SH"]


def build_watchlist_issues(watchlist: pd.DataFrame) -> pd.DataFrame:
    rows = []
    missing_columns = [column for column in REQUIRED_WATCHLIST_COLUMNS if column not in watchlist.columns]
    for column in missing_columns:
        rows.append({"位置": "表头", "问题": f"缺少字段 {column}", "字段": column})

    for index, row in watchlist.iterrows():
        csv_line = index + 2
        for column in REQUIRED_WATCHLIST_COLUMNS:
            if column not in watchlist.columns:
                continue
            value = row.get(column)
            if pd.isna(value) or str(value).strip() == "":
                rows.append({"位置": f"第{csv_line}行", "问题": f"{column} 为空", "字段": column})

    existing_categories = set(watchlist["category"].dropna().astype(str).str.strip()) if "category" in watchlist.columns else set()
    for category in REQUIRED_CATEGORIES:
        if category not in existing_categories:
            rows.append({"位置": "category", "问题": f"缺少 category：{category}", "字段": "category"})

    return pd.DataFrame(rows)


def build_etf_issues(etf_config: pd.DataFrame) -> pd.DataFrame:
    rows = []
    required_columns = ["name", "ticker", "manual_iopv", "manual_nav"]
    for column in required_columns:
        if column not in etf_config.columns:
            rows.append({"位置": "表头", "问题": f"缺少字段 {column}", "字段": column})

    if "ticker" in etf_config.columns:
        existing_tickers = set(etf_config["ticker"].dropna().astype(str).str.strip())
    else:
        existing_tickers = set()

    for ticker in REQUIRED_ETF_TICKERS:
        if ticker not in existing_tickers:
            rows.append({"位置": "ticker", "问题": f"缺少 ETF：{ticker}", "字段": "ticker"})

    for index, row in etf_config.iterrows():
        csv_line = index + 2
        for column in ["name", "ticker"]:
            if column not in etf_config.columns:
                continue
            value = row.get(column)
            if pd.isna(value) or str(value).strip() == "":
                rows.append({"位置": f"第{csv_line}行", "问题": f"{column} 为空", "字段": column})

    return pd.DataFrame(rows)


def render_config_check(watchlist: pd.DataFrame, etf_config: pd.DataFrame) -> None:
    st.subheader("配置检查")

    watchlist_issues = build_watchlist_issues(watchlist)
    etf_issues = build_etf_issues(etf_config)
    missing_field_count = len(watchlist_issues) + len(etf_issues)
    category_count = watchlist["category"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()

    summary = pd.DataFrame(
        [
            {"指标": "股票池数量", "数量": len(watchlist)},
            {"指标": "ETF数量", "数量": len(etf_config)},
            {"指标": "category数量", "数量": category_count},
            {"指标": "缺失字段数量", "数量": missing_field_count},
        ]
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)

    if missing_field_count == 0:
        st.success("配置检查通过。")
    else:
        st.error(f"配置检查发现 {missing_field_count} 个问题。")

    st.write("必需 category")
    category_status = pd.DataFrame(
        [
            {
                "category": category,
                "状态": "存在"
                if "category" in watchlist.columns
                and category in set(watchlist["category"].dropna().astype(str).str.strip())
                else "缺失",
            }
            for category in REQUIRED_CATEGORIES
        ]
    )
    st.dataframe(category_status, use_container_width=True, hide_index=True)

    st.write("watchlist.csv 问题")
    if watchlist_issues.empty:
        st.info("watchlist.csv 未发现字段或空值问题。")
    else:
        st.dataframe(watchlist_issues, use_container_width=True, hide_index=True)

    st.write("etf_config.csv 问题")
    if etf_issues.empty:
        st.info("etf_config.csv 未发现字段或 ETF 代码问题。")
    else:
        st.dataframe(etf_issues, use_container_width=True, hide_index=True)


def render_industry_home(
    industry_chain_data: pd.DataFrame,
    watchlist: pd.DataFrame,
    dashboard_data: Optional[pd.DataFrame] = None,
    us_dashboard_data: Optional[pd.DataFrame] = None,
) -> None:
    st.subheader("产业链首页")
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
            "business": "业务",
            "market_focus": "市场关注",
            "description": "一句话说明",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)


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

    category_order = [category for category in REQUIRED_CATEGORIES if category in set(watchlist["category"].dropna().astype(str))]
    extra_categories = [
        category
        for category in sorted(watchlist["category"].dropna().astype(str).unique())
        if category not in category_order
    ]

    for category in category_order + extra_categories:
        members = watchlist[watchlist["category"].eq(category)].copy()
        with st.expander(f"{category}（{len(members)}家公司）", expanded=False):
            for _, row in members.iterrows():
                st.markdown(f"#### {row['name']}")
                st.caption(f"{row['ticker']} · {row['market']}")
                st.write(f"主营业务：{row['business']}")
                st.write(f"市场关注：{row['market_focus']}")
                st.write(f"一句话理解：{row['description']}")
                st.divider()


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
    category_order = [category for category in REQUIRED_CATEGORIES if category in set(watchlist["category"].dropna().astype(str))]
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


def render_ai_industry_chain_map(watchlist: pd.DataFrame, events: pd.DataFrame) -> None:
    st.subheader("AI产业链地图")
    st.caption("本页面用于展示 AI基础设施产业链上下游关系，不展示实时行情。")

    chain_order = ["云厂Capex", "GPU", "HBM", "交换机/ASIC", "光模块", "光器件", "PCB"]
    event_map = {
        category: events[events["industry"].eq(category)].copy()
        for category in events["industry"].dropna().astype(str).unique()
    }

    for index, category in enumerate(chain_order):
        members = watchlist[watchlist["category"].eq(category)].copy()
        related_events = event_map.get(category, pd.DataFrame())
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

        if index < len(chain_order) - 1:
            st.markdown("### ↓")

    st.caption("本页面为本地产业链知识图谱，不构成投资建议。")


def render_market_monitor(
    dashboard_data: pd.DataFrame,
    us_dashboard_data: pd.DataFrame,
    a_share_watchlist: pd.DataFrame,
    data_layer,
) -> None:
    if (dashboard_data is None or dashboard_data.empty) and (us_dashboard_data is None or us_dashboard_data.empty):
        st.info("暂无缓存，请点击刷新。")

    st.subheader("A股行情")
    if dashboard_data is None or dashboard_data.empty:
        st.info("A股暂无缓存，请点击刷新。")
    else:
        a_share_display = dashboard_data.copy()
        a_share_display["观察结论"] = a_share_display["change_pct"].apply(classify_selloff)
        a_share_display["状态"] = a_share_display.apply(summarize_status, axis=1)
        a_share_display = a_share_display.rename(
            columns={
                "name": "名称",
                "ticker": "代码",
                "market": "市场",
                "theme": "主题",
                "category": "产业链",
                "latest_price": "最新价",
                "change_pct": "涨跌幅%",
                "turnover": "成交额",
                "ma20": "20日均线",
                "ma60": "60日均线",
            }
        )
        a_share_display["成交额"] = a_share_display["成交额"].apply(format_turnover)
        a_share_display["20日均线"] = a_share_display["20日均线"].apply(format_optional_number)
        a_share_display["60日均线"] = a_share_display["60日均线"].apply(format_optional_number)

        st.dataframe(
            a_share_display[
                ["名称", "代码", "市场", "主题", "产业链", "最新价", "涨跌幅%", "成交额", "20日均线", "60日均线", "观察结论", "状态"]
            ],
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("历史日线数据状态", expanded=False):
            st.dataframe(
                data_layer.local_history_status(a_share_watchlist.to_dict("records")),
                use_container_width=True,
                hide_index=True,
            )
            st.caption("20日/60日均线需要至少 60 条历史日线收盘价。本地文件放在 data/history 文件夹。")

    st.subheader("美股行情")
    if us_dashboard_data is None or us_dashboard_data.empty:
        st.info("美股暂无缓存，请点击刷新。")
        return

    us_display = us_dashboard_data.copy()
    us_display = us_display.rename(
        columns={
            "name": "名称",
            "ticker": "代码",
            "market": "市场",
            "theme": "主题",
            "category": "产业链",
            "latest_price": "最新价",
            "change_pct": "日涨跌幅%",
            "volume": "成交量",
            "status": "状态",
        }
    )
    us_display["最新价"] = us_display["最新价"].apply(format_optional_number)
    us_display["日涨跌幅%"] = us_display["日涨跌幅%"].apply(format_optional_number)
    us_display["成交量"] = us_display["成交量"].apply(format_volume)

    st.dataframe(
        us_display[["名称", "代码", "市场", "主题", "产业链", "最新价", "日涨跌幅%", "成交量", "状态"]],
        use_container_width=True,
        hide_index=True,
    )

def render_etf_monitor(etf_premium_data: pd.DataFrame) -> None:
    st.subheader("ETF溢价监控")
    if etf_premium_data is None or etf_premium_data.empty:
        st.info("暂无缓存，请点击刷新。")
        return

    warning_rows = etf_premium_data[etf_premium_data["premium_rate"] > 10]
    if not warning_rows.empty:
        warning_names = "、".join(warning_rows["name"].astype(str).tolist())
        st.error(f"{warning_names} 溢价率超过10%，注意溢价风险。")

    display = etf_premium_data.rename(
        columns={
            "name": "名称",
            "ticker": "代码",
            "latest_price": "市场价格",
            "iopv": "IOPV",
            "nav": "净值",
            "valuation_source": "估值来源",
            "premium_rate": "溢价率",
            "risk": "风险等级",
            "status": "状态",
        }
    )
    display["市场价格"] = display["市场价格"].apply(format_optional_number)
    display["IOPV"] = display["IOPV"].apply(format_optional_number)
    display["净值"] = display["净值"].apply(format_optional_number)
    display["溢价率"] = display["溢价率"].apply(format_percent)

    st.dataframe(
        display[["名称", "代码", "市场价格", "IOPV", "净值", "估值来源", "溢价率", "风险等级", "状态"]],
        use_container_width=True,
        hide_index=True,
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
    ordered_categories = [category for category in REQUIRED_CATEGORIES if category in set(industry_display["产业链"].astype(str))]
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


def render_next_steps() -> None:
    st.subheader("下一阶段")
    st.write("接下来进入 P1：美股联动、产业链百科，以及产业链首页的进一步增强。")
