from pathlib import Path

import pandas as pd

from config.constants import REQUIRED_CHAIN_RELATION_COLUMNS

from .utils import timed_log


CHAIN_RELATIONS_FILE = "chain_relations.csv"


@timed_log
def load_chain_relations() -> pd.DataFrame:
    path = Path(CHAIN_RELATIONS_FILE)
    if not path.exists():
        return pd.DataFrame(columns=REQUIRED_CHAIN_RELATION_COLUMNS)

    relations = pd.read_csv(path)
    for column in REQUIRED_CHAIN_RELATION_COLUMNS:
        if column not in relations.columns:
            relations[column] = ""
    return relations[REQUIRED_CHAIN_RELATION_COLUMNS]
