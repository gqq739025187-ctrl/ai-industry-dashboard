REQUIRED_WATCHLIST_COLUMNS = [
    "name",
    "ticker",
    "market",
    "theme",
    "category",
    "tier",
    "business",
    "market_focus",
    "description",
    "core_customer",
    "upstream",
    "downstream",
    "bull_case",
    "bear_case",
    "confidence",
]

REQUIRED_CATEGORIES = [
    "云厂Capex",
    "GPU",
    "HBM",
    "光模块",
    "光器件",
    "交换机/ASIC",
    "PCB",
    "CCL",
    "液冷",
    "服务器ODM",
    "光纤光缆",
    "连接器",
    "电源",
    "存储链",
    "ETF映射",
]

REQUIRED_ETF_TICKERS = ["513310.SH", "515880.SH", "513520.SH"]

REQUIRED_CHAIN_RELATION_COLUMNS = [
    "source_category",
    "target_category",
    "relation_type",
    "description",
    "importance",
]

REQUIRED_MARKET_EXPECTATION_COLUMNS = [
    "category",
    "logic_score",
    "cycle_score",
    "sentiment_score",
    "valuation_score",
    "expectation_level",
    "note",
]

REQUIRED_EVENT_IMPACT_MATRIX_COLUMNS = [
    "event",
    "category",
    "direction",
    "strength",
    "time_horizon",
    "description",
]

REQUIRED_DRIVER_COLUMNS = [
    "driver",
    "category",
    "direction",
    "importance",
    "leading_or_lagging",
    "description",
]

CATEGORY_ORDER = REQUIRED_CATEGORIES

CHAIN_ORDER = ["云厂Capex", "GPU", "HBM", "交换机/ASIC", "光模块", "光器件", "PCB"]
