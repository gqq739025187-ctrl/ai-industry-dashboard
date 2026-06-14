from __future__ import annotations

import contextlib
import importlib
import io
import os
import re
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_EVENTS_COLUMNS = ["event_name", "industry", "impact_level", "description"]
REQUIRED_ETF_COLUMNS = ["name", "ticker", "manual_iopv", "manual_nav"]
VALID_EVENT_DIRECTIONS = ["positive", "negative", "neutral"]
VALID_LEADING_LAGGING = ["leading", "lagging"]
VALID_TIERS = ["S", "A", "B", "C", ""]
VALID_BOOL_TEXT = ["true", "false"]


def print_ok(message: str) -> None:
    print(f"✅ {message}")


def print_fail(message: str) -> None:
    print(f"❌ {message}")


def import_module(name: str, label: str) -> bool:
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            importlib.import_module(name)
        print_ok(f"{label} 导入成功")
        return True
    except Exception as error:
        print_fail(f"{label} 导入失败：{error}")
        return False


def read_csv(filename: str, label: str) -> pd.DataFrame | None:
    path = PROJECT_ROOT / filename
    try:
        data = pd.read_csv(path)
        print_ok(f"{filename} 读取成功，共 {len(data)} 行")
        return data
    except Exception as error:
        print_fail(f"{filename} 读取失败：{error}")
        return None


def check_columns(data: pd.DataFrame | None, required_columns: list[str], label: str) -> bool:
    if data is None:
        return False
    missing = [column for column in required_columns if column not in data.columns]
    if missing:
        print_fail(f"{label} 字段缺失：{', '.join(missing)}")
        return False
    print_ok(f"{label} 字段完整")
    return True


def check_required_values(
    data: pd.DataFrame | None,
    column: str,
    required_values: list[str],
    label: str,
    coverage_aliases: dict[str, list[str]] | None = None,
) -> bool:
    if data is None:
        return False
    if column not in data.columns:
        print_fail(f"{label} 检查失败：缺少字段 {column}")
        return False
    existing_values = set(data[column].dropna().astype(str).str.strip())
    aliases = coverage_aliases or {}
    missing = [
        value
        for value in required_values
        if value not in existing_values and not any(alias in existing_values for alias in aliases.get(value, []))
    ]
    if missing:
        print_fail(f"{label} 缺失：{', '.join(missing)}")
        return False
    print_ok(f"{label} 完整")
    return True


def check_relation_categories(relations: pd.DataFrame | None, allowed_categories: list[str]) -> bool:
    if relations is None:
        return False
    allowed = set(allowed_categories)
    invalid_rows = []
    for index, row in relations.iterrows():
        source = str(row.get("source_category", "")).strip()
        target = str(row.get("target_category", "")).strip()
        if source not in allowed or target not in allowed:
            invalid_rows.append(f"第{index + 2}行 {source}->{target}")
    if invalid_rows:
        print_fail(f"chain_relations.csv 分类不合法：{'; '.join(invalid_rows)}")
        return False
    print_ok("chain_relations.csv 分类合法")
    return True


def check_relation_importance(relations: pd.DataFrame | None) -> bool:
    if relations is None:
        return False
    values = pd.to_numeric(relations.get("importance"), errors="coerce")
    invalid = values.isna()
    if invalid.any():
        rows = [str(index + 2) for index in relations.index[invalid]]
        print_fail(f"chain_relations.csv importance 不是数字：第 {', '.join(rows)} 行")
        return False
    print_ok("chain_relations.csv importance 可转为数字")
    return True


def check_category_values(data: pd.DataFrame | None, column: str, allowed_categories: list[str], label: str) -> bool:
    if data is None:
        return False
    if column not in data.columns:
        print_fail(f"{label} 检查失败：缺少字段 {column}")
        return False
    allowed = set(allowed_categories)
    invalid_rows = []
    for index, value in data[column].items():
        category = str(value).strip()
        if category not in allowed:
            invalid_rows.append(f"第{index + 2}行 {category}")
    if invalid_rows:
        print_fail(f"{label} 分类不合法：{'; '.join(invalid_rows)}")
        return False
    print_ok(f"{label} 分类合法")
    return True


def check_numeric_columns(data: pd.DataFrame | None, columns: list[str], label: str) -> bool:
    if data is None:
        return False
    invalid_messages = []
    for column in columns:
        values = pd.to_numeric(data.get(column), errors="coerce")
        invalid = values.isna()
        if invalid.any():
            rows = [str(index + 2) for index in data.index[invalid]]
            invalid_messages.append(f"{column}: 第 {', '.join(rows)} 行")
    if invalid_messages:
        print_fail(f"{label} 数值字段异常：{'; '.join(invalid_messages)}")
        return False
    print_ok(f"{label} 数值字段可转为数字")
    return True


def check_non_empty_column(data: pd.DataFrame | None, column: str, label: str) -> bool:
    if data is None:
        return False
    if column not in data.columns:
        print_fail(f"{label} 检查失败：缺少字段 {column}")
        return False
    empty = data[column].isna() | data[column].astype(str).str.strip().eq("")
    if empty.any():
        rows = [str(index + 2) for index in data.index[empty]]
        print_fail(f"{label} 存在空值：第 {', '.join(rows)} 行")
        return False
    print_ok(f"{label} 非空")
    return True


def check_allowed_values(data: pd.DataFrame | None, column: str, allowed_values: list[str], label: str) -> bool:
    if data is None:
        return False
    if column not in data.columns:
        print_fail(f"{label} 检查失败：缺少字段 {column}")
        return False
    allowed = set(allowed_values)
    invalid_rows = []
    for index, value in data[column].items():
        item = str(value).strip()
        if item not in allowed:
            invalid_rows.append(f"第{index + 2}行 {item}")
    if invalid_rows:
        print_fail(f"{label} 值不合法：{'; '.join(invalid_rows)}")
        return False
    print_ok(f"{label} 合法")
    return True


def check_bool_text_values(data: pd.DataFrame | None, column: str, label: str) -> bool:
    if data is None:
        return False
    if column not in data.columns:
        print_fail(f"{label} 检查失败：缺少字段 {column}")
        return False
    invalid_rows = []
    for index, value in data[column].items():
        item = str(value).strip().lower()
        if item not in VALID_BOOL_TEXT:
            invalid_rows.append(f"第{index + 2}行 {value}")
    if invalid_rows:
        print_fail(f"{label} 不是 true/false：{'; '.join(invalid_rows)}")
        return False
    print_ok(f"{label} 可识别为 true/false")
    return True


def check_no_enabled_auth_public_rss(sources: pd.DataFrame | None) -> bool:
    if sources is None:
        return False
    invalid_rows = []
    for index, row in sources.iterrows():
        enabled = str(row.get("enabled", "")).strip().lower() == "true"
        requires_auth = str(row.get("requires_auth", "")).strip().lower() == "true"
        access_type = str(row.get("access_type", "")).strip()
        feed_type = str(row.get("feed_type", "")).strip()
        if enabled and requires_auth and access_type == "public_rss" and feed_type == "rss":
            invalid_rows.append(str(index + 2))
    if invalid_rows:
        print_fail(f"unified_sources.csv public_rss 含启用且需认证来源：第 {', '.join(invalid_rows)} 行")
        return False
    print_ok("unified_sources.csv public_rss 未启用需认证来源")
    return True


def check_credential_env_keys(sources: pd.DataFrame | None) -> bool:
    if sources is None:
        return False
    pattern = re.compile(r"^[A-Z][A-Z0-9_]*$")
    invalid_rows = []
    for index, value in sources.get("credential_env_key", pd.Series(dtype=str)).items():
        item = str(value).strip()
        if not item or item.lower() == "nan":
            continue
        if not pattern.match(item):
            invalid_rows.append(f"第{index + 2}行 {item}")
    if invalid_rows:
        print_fail(f"credential_env_key 只能写环境变量名：{'; '.join(invalid_rows)}")
        return False
    print_ok("credential_env_key 未发现疑似真实密钥")
    return True


def report_watchlist_counts(watchlist: pd.DataFrame | None) -> bool:
    if watchlist is None:
        return False
    if "market" not in watchlist.columns or "tier" not in watchlist.columns:
        print_fail("watchlist.csv 数量统计失败：缺少 market 或 tier")
        return False
    a_share_count = int(watchlist["market"].astype(str).eq("A股").sum())
    overseas_anchor_count = int(
        ((~watchlist["market"].astype(str).isin(["A股", "ETF"])) & watchlist["tier"].astype(str).eq("S")).sum()
    )
    print_ok(f"A股公司数量：{a_share_count}")
    print_ok(f"海外锚点数量：{overseas_anchor_count}")
    return True


def main() -> int:
    os.chdir(PROJECT_ROOT)
    sys.path.insert(0, str(PROJECT_ROOT))

    checks: list[bool] = []

    checks.append(import_module("app", "app.py"))
    checks.append(import_module("data_layer", "data_layer.py"))
    checks.append(import_module("dashboard.views", "dashboard.views"))
    checks.append(import_module("config.constants", "config.constants"))

    from config.constants import (
        CATEGORY_COVERAGE_ALIASES,
        CHAIN_ORDER,
        REQUIRED_CATEGORIES,
        REQUIRED_CHAIN_RELATION_COLUMNS,
        REQUIRED_DRIVER_COLUMNS,
        REQUIRED_EVENT_IMPACT_MATRIX_COLUMNS,
        REQUIRED_ETF_TICKERS,
        REQUIRED_LAYERS,
        REQUIRED_MARKET_EXPECTATION_COLUMNS,
        REQUIRED_RAW_NEWS_COLUMNS,
        REQUIRED_UNIFIED_SOURCE_COLUMNS,
        VALID_ACCESS_TYPES,
        VALID_AUTH_METHODS,
        VALID_FEED_TYPES,
        VALID_RAW_NEWS_STATUS,
        VALID_SOURCE_TYPES,
        REQUIRED_WATCHLIST_COLUMNS,
    )

    watchlist = read_csv("watchlist.csv", "watchlist.csv")
    events = read_csv("events.csv", "events.csv")
    event_impact_matrix = read_csv("event_impact_matrix.csv", "event_impact_matrix.csv")
    drivers = read_csv("drivers.csv", "drivers.csv")
    etf_config = read_csv("etf_config.csv", "etf_config.csv")
    chain_relations = read_csv("chain_relations.csv", "chain_relations.csv")
    market_expectation = read_csv("market_expectation.csv", "market_expectation.csv")
    unified_sources = read_csv("unified_sources.csv", "unified_sources.csv")
    raw_news = read_csv("raw_news.csv", "raw_news.csv")
    allowed_categories = list(dict.fromkeys(REQUIRED_CATEGORIES + CHAIN_ORDER))

    checks.append(check_columns(watchlist, REQUIRED_WATCHLIST_COLUMNS, "watchlist.csv"))
    checks.append(check_columns(events, REQUIRED_EVENTS_COLUMNS, "events.csv"))
    checks.append(check_columns(event_impact_matrix, REQUIRED_EVENT_IMPACT_MATRIX_COLUMNS, "event_impact_matrix.csv"))
    checks.append(check_columns(drivers, REQUIRED_DRIVER_COLUMNS, "drivers.csv"))
    checks.append(check_columns(etf_config, REQUIRED_ETF_COLUMNS, "etf_config.csv"))
    checks.append(check_columns(chain_relations, REQUIRED_CHAIN_RELATION_COLUMNS, "chain_relations.csv"))
    checks.append(check_columns(market_expectation, REQUIRED_MARKET_EXPECTATION_COLUMNS, "market_expectation.csv"))
    checks.append(check_columns(unified_sources, REQUIRED_UNIFIED_SOURCE_COLUMNS, "unified_sources.csv"))
    checks.append(check_columns(raw_news, REQUIRED_RAW_NEWS_COLUMNS, "raw_news.csv"))
    checks.append(
        check_required_values(
            watchlist,
            "category",
            REQUIRED_CATEGORIES,
            "必需 category",
            CATEGORY_COVERAGE_ALIASES,
        )
    )
    checks.append(check_allowed_values(watchlist, "tier", VALID_TIERS, "watchlist.csv tier"))
    checks.append(check_allowed_values(watchlist, "layer", REQUIRED_LAYERS, "watchlist.csv layer"))
    checks.append(check_non_empty_column(watchlist, "subcategory", "watchlist.csv subcategory"))
    checks.append(report_watchlist_counts(watchlist))
    checks.append(check_required_values(etf_config, "ticker", REQUIRED_ETF_TICKERS, "必需 ETF"))
    checks.append(check_relation_categories(chain_relations, allowed_categories))
    checks.append(check_relation_importance(chain_relations))
    checks.append(check_category_values(event_impact_matrix, "category", allowed_categories, "event_impact_matrix.csv"))
    checks.append(check_numeric_columns(event_impact_matrix, ["strength"], "event_impact_matrix.csv"))
    checks.append(check_allowed_values(event_impact_matrix, "direction", VALID_EVENT_DIRECTIONS, "event_impact_matrix.csv direction"))
    checks.append(check_category_values(drivers, "category", allowed_categories, "drivers.csv"))
    checks.append(check_numeric_columns(drivers, ["importance"], "drivers.csv"))
    checks.append(check_allowed_values(drivers, "direction", VALID_EVENT_DIRECTIONS, "drivers.csv direction"))
    checks.append(check_allowed_values(drivers, "leading_or_lagging", VALID_LEADING_LAGGING, "drivers.csv leading_or_lagging"))
    checks.append(check_category_values(market_expectation, "category", allowed_categories, "market_expectation.csv"))
    checks.append(
        check_numeric_columns(
            market_expectation,
            ["logic_score", "cycle_score", "sentiment_score", "valuation_score"],
            "market_expectation.csv",
        )
    )
    checks.append(check_non_empty_column(market_expectation, "expectation_level", "market_expectation.csv expectation_level"))
    checks.append(check_allowed_values(unified_sources, "source_type", VALID_SOURCE_TYPES, "unified_sources.csv source_type"))
    checks.append(check_allowed_values(unified_sources, "access_type", VALID_ACCESS_TYPES, "unified_sources.csv access_type"))
    checks.append(check_allowed_values(unified_sources, "feed_type", VALID_FEED_TYPES, "unified_sources.csv feed_type"))
    checks.append(check_allowed_values(unified_sources, "auth_method", VALID_AUTH_METHODS, "unified_sources.csv auth_method"))
    checks.append(check_bool_text_values(unified_sources, "enabled", "unified_sources.csv enabled"))
    checks.append(check_bool_text_values(unified_sources, "requires_auth", "unified_sources.csv requires_auth"))
    checks.append(check_numeric_columns(unified_sources, ["credibility"], "unified_sources.csv"))
    checks.append(check_allowed_values(raw_news, "status", VALID_RAW_NEWS_STATUS, "raw_news.csv status"))
    checks.append(check_no_enabled_auth_public_rss(unified_sources))
    checks.append(check_credential_env_keys(unified_sources))

    if all(checks):
        print("\n健康检查通过。")
        return 0

    print("\n健康检查未通过，请根据上面的失败项修正。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
