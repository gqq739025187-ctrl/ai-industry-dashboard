from pathlib import Path

import pandas as pd

from config.constants import REQUIRED_DRIVER_COLUMNS

from .utils import timed_log


DRIVERS_FILE = "drivers.csv"


@timed_log
def load_drivers() -> pd.DataFrame:
    path = Path(DRIVERS_FILE)
    if not path.exists():
        return pd.DataFrame(columns=REQUIRED_DRIVER_COLUMNS)

    drivers = pd.read_csv(path)
    for column in REQUIRED_DRIVER_COLUMNS:
        if column not in drivers.columns:
            drivers[column] = ""
    drivers["importance"] = pd.to_numeric(drivers["importance"], errors="coerce")
    return drivers[REQUIRED_DRIVER_COLUMNS]
