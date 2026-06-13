import pandas as pd

from .utils import timed_log


EVENTS_FILE = "events.csv"
EVENT_COLUMNS = ["event_name", "industry", "impact_level", "description"]


@timed_log
def load_events() -> pd.DataFrame:
    events = pd.read_csv(EVENTS_FILE)
    for column in EVENT_COLUMNS:
        if column not in events.columns:
            events[column] = ""
    return events[EVENT_COLUMNS]


def map_events_to_companies(events: pd.DataFrame, watchlist: pd.DataFrame) -> pd.DataFrame:
    if events is None or events.empty:
        return pd.DataFrame()

    mapped = events.copy()
    mapped["受影响公司"] = mapped["industry"].apply(
        lambda industry: "、".join(watchlist[watchlist["category"].eq(industry)]["name"].astype(str).tolist()) or "暂无映射"
    )
    return mapped
