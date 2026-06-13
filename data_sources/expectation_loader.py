from pathlib import Path

import pandas as pd

from config.constants import REQUIRED_MARKET_EXPECTATION_COLUMNS

from .utils import timed_log


MARKET_EXPECTATION_FILE = "market_expectation.csv"
SCORE_COLUMNS = ["logic_score", "cycle_score", "sentiment_score", "valuation_score"]


@timed_log
def load_market_expectation() -> pd.DataFrame:
    path = Path(MARKET_EXPECTATION_FILE)
    if not path.exists():
        return pd.DataFrame(columns=REQUIRED_MARKET_EXPECTATION_COLUMNS)

    expectation = pd.read_csv(path)
    for column in REQUIRED_MARKET_EXPECTATION_COLUMNS:
        if column not in expectation.columns:
            expectation[column] = ""
    for column in SCORE_COLUMNS:
        expectation[column] = pd.to_numeric(expectation[column], errors="coerce")
    return expectation[REQUIRED_MARKET_EXPECTATION_COLUMNS]
