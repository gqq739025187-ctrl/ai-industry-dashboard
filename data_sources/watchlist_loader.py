import pandas as pd

from config.constants import CATEGORY_COVERAGE_ALIASES, REQUIRED_CATEGORIES, REQUIRED_WATCHLIST_COLUMNS

from .utils import timed_log


WATCHLIST_FILE = "watchlist.csv"


def category_is_covered(category: str, existing_categories: set[str]) -> bool:
    return category in existing_categories or any(
        alias in existing_categories for alias in CATEGORY_COVERAGE_ALIASES.get(category, [])
    )


@timed_log
def load_watchlist() -> pd.DataFrame:
    watchlist = pd.read_csv(WATCHLIST_FILE)
    for column in REQUIRED_WATCHLIST_COLUMNS:
        if column not in watchlist.columns:
            watchlist[column] = ""
    return watchlist[REQUIRED_WATCHLIST_COLUMNS]


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
