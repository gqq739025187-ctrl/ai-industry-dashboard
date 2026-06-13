from pathlib import Path

import pandas as pd

from config.constants import REQUIRED_EVENT_IMPACT_MATRIX_COLUMNS

from .utils import timed_log


EVENT_IMPACT_MATRIX_FILE = "event_impact_matrix.csv"


@timed_log
def load_event_impact_matrix() -> pd.DataFrame:
    path = Path(EVENT_IMPACT_MATRIX_FILE)
    if not path.exists():
        return pd.DataFrame(columns=REQUIRED_EVENT_IMPACT_MATRIX_COLUMNS)

    matrix = pd.read_csv(path)
    for column in REQUIRED_EVENT_IMPACT_MATRIX_COLUMNS:
        if column not in matrix.columns:
            matrix[column] = ""
    matrix["strength"] = pd.to_numeric(matrix["strength"], errors="coerce")
    return matrix[REQUIRED_EVENT_IMPACT_MATRIX_COLUMNS]
