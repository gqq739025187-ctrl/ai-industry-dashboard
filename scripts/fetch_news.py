from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from data_sources.news_fetcher import fetch_public_rss_sources  # noqa: E402


def main() -> int:
    result = fetch_public_rss_sources()
    print("可信源消息抓取完成")
    print(f"来源数量：{result['source_count']}")
    print(f"本次抓取条目：{result['fetched_count']}")
    print(f"新增条目：{result['new_count']}")
    print(f"重复条目：{result['duplicate_count']}")
    if result["failed_sources"]:
        print("失败来源：")
        for source in result["failed_sources"]:
            print(f"- {source}")
    else:
        print("失败来源：无")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
