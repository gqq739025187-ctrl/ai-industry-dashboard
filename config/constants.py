REQUIRED_WATCHLIST_COLUMNS = [
    "name",
    "ticker",
    "market",
    "theme",
    "category",
    "layer",
    "subcategory",
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
    "ASIC",
    "HBM",
    "存储链",
    "光模块",
    "光器件",
    "光纤光缆",
    "交换机/ASIC",
    "PCB",
    "CCL",
    "连接器",
    "电源",
    "液冷",
    "服务器ODM",
    "ETF映射",
]

REQUIRED_LAYERS = [
    "Demand",
    "Compute",
    "Memory",
    "Packaging",
    "Network",
    "Optical",
    "Electronic",
    "PowerCooling",
    "Manufacturing",
    "Semiconductor Equipment",
    "ETF",
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

REQUIRED_UNIFIED_SOURCE_COLUMNS = [
    "source_name",
    "source_type",
    "access_type",
    "feed_type",
    "url",
    "enabled",
    "credibility",
    "requires_auth",
    "auth_method",
    "credential_env_key",
    "allowed_scope",
    "note",
]

REQUIRED_RAW_NEWS_COLUMNS = [
    "fetch_time",
    "published_time",
    "source_name",
    "source_type",
    "access_type",
    "title",
    "summary",
    "url",
    "raw_text",
    "detected_keywords",
    "detected_layer",
    "detected_category",
    "event_type",
    "status",
]

VALID_SOURCE_TYPES = [
    "公司官方",
    "财报电话会",
    "交易所公告",
    "投行研报",
    "产业媒体",
    "权威财经媒体",
    "监管披露",
    "央行",
    "财政部",
    "官方统计",
    "数据商",
]

VALID_ACCESS_TYPES = ["public_rss", "public_api", "email_feed", "authenticated_source"]
VALID_FEED_TYPES = ["rss", "api", "email", "browser", "manual"]
VALID_AUTH_METHODS = ["none", "api_key", "oauth", "email", "browser_session"]
VALID_RAW_NEWS_STATUS = ["pending_review", "ignored", "extracted", "confirmed"]

CATEGORY_ORDER = REQUIRED_CATEGORIES

CHAIN_ORDER = [
    "云厂Capex",
    "GPU",
    "ASIC",
    "HBM",
    "存储链",
    "交换机/ASIC",
    "光模块",
    "光器件",
    "光纤光缆",
    "PCB",
    "CCL",
    "连接器",
    "电源",
    "液冷",
    "服务器ODM",
    "ETF映射",
]

CATEGORY_COVERAGE_ALIASES = {
    "ASIC": ["交换机/ASIC"],
}
