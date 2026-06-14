from pathlib import Path

import pandas as pd

from config.constants import REQUIRED_RAW_NEWS_COLUMNS, REQUIRED_UNIFIED_SOURCE_COLUMNS

from .utils import timed_log


UNIFIED_SOURCES_FILE = "unified_sources.csv"
RAW_NEWS_FILE = "raw_news.csv"


def parse_bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def ensure_columns(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in data.columns:
            data[column] = ""
    return data[columns]


@timed_log
def load_unified_sources() -> pd.DataFrame:
    path = Path(UNIFIED_SOURCES_FILE)
    if not path.exists():
        return pd.DataFrame(columns=REQUIRED_UNIFIED_SOURCE_COLUMNS)

    sources = ensure_columns(pd.read_csv(path), REQUIRED_UNIFIED_SOURCE_COLUMNS)
    sources["enabled"] = sources["enabled"].apply(parse_bool)
    sources["requires_auth"] = sources["requires_auth"].apply(parse_bool)
    sources["credibility"] = pd.to_numeric(sources["credibility"], errors="coerce")
    return sources


@timed_log
def load_raw_news() -> pd.DataFrame:
    path = Path(RAW_NEWS_FILE)
    if not path.exists():
        return pd.DataFrame(columns=REQUIRED_RAW_NEWS_COLUMNS)

    return ensure_columns(pd.read_csv(path), REQUIRED_RAW_NEWS_COLUMNS)


@timed_log
def save_raw_news(raw_news: pd.DataFrame) -> None:
    data = ensure_columns(raw_news.copy(), REQUIRED_RAW_NEWS_COLUMNS)
    data.to_csv(RAW_NEWS_FILE, index=False)
