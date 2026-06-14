import pandas as pd
import streamlit as st

from config.constants import (
    CATEGORY_COVERAGE_ALIASES,
    REQUIRED_CATEGORIES,
    REQUIRED_ETF_TICKERS,
    REQUIRED_LAYERS,
    REQUIRED_WATCHLIST_COLUMNS,
)


def category_is_covered(category: str, existing_categories: set[str]) -> bool:
    return category in existing_categories or any(
        alias in existing_categories for alias in CATEGORY_COVERAGE_ALIASES.get(category, [])
    )


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
        if not category_is_covered(category, existing_categories):
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
    layer_count = watchlist["layer"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique()

    summary = pd.DataFrame(
        [
            {"指标": "股票池数量", "数量": len(watchlist)},
            {"指标": "ETF数量", "数量": len(etf_config)},
            {"指标": "layer数量", "数量": layer_count},
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
                and category_is_covered(category, set(watchlist["category"].dropna().astype(str).str.strip()))
                else "缺失",
            }
            for category in REQUIRED_CATEGORIES
        ]
    )
    st.dataframe(category_status, use_container_width=True, hide_index=True)

    st.write("Layer 覆盖")
    existing_layers = set(watchlist["layer"].dropna().astype(str).str.strip()) if "layer" in watchlist.columns else set()
    layer_status = pd.DataFrame(
        [
            {
                "Layer": layer,
                "状态": "存在" if layer in existing_layers else "缺失",
                "公司数量": int(watchlist["layer"].astype(str).eq(layer).sum()) if "layer" in watchlist.columns else 0,
            }
            for layer in REQUIRED_LAYERS
        ]
    )
    st.dataframe(layer_status, use_container_width=True, hide_index=True)

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
