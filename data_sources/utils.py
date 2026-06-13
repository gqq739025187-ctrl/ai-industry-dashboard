from datetime import datetime
from functools import wraps
import time

import pandas as pd


def timed_log(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        start_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[耗时日志] {func.__name__} 开始: {start_text}")
        try:
            return func(*args, **kwargs)
        finally:
            end = time.time()
            end_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[耗时日志] {func.__name__} 结束: {end_text}; 耗时: {end - start:.2f}秒")

    return wrapper


def parse_optional_float(value):
    if pd.isna(value) or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_float(value, default=None):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def format_optional_number(value) -> str:
    parsed = safe_float(value)
    if parsed is None:
        return "待获取"
    return f"{parsed:.2f}"
