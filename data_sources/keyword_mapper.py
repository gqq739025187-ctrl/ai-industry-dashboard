KEYWORD_RULES = [
    {
        "keywords": ["capex", "capital expenditure", "data center", "ai infrastructure"],
        "layer": "Demand",
        "category": "云厂Capex",
        "event_type": "Capex",
    },
    {
        "keywords": ["nvidia", "gpu", "accelerator"],
        "layer": "Compute",
        "category": "GPU",
        "event_type": "Industry",
    },
    {
        "keywords": ["hbm"],
        "layer": "Memory",
        "category": "HBM",
        "event_type": "SupplyDemand",
    },
    {
        "keywords": ["dram", "nand", "memory"],
        "layer": "Memory",
        "category": "存储链",
        "event_type": "SupplyDemand",
    },
    {
        "keywords": ["federal reserve", "rate", "inflation", "cpi", "jobs"],
        "layer": "Macro",
        "category": "宏观流动性",
        "event_type": "Macro",
    },
    {
        "keywords": ["treasury", "deficit", "bond issuance", "debt"],
        "layer": "Macro",
        "category": "美国财政",
        "event_type": "Fiscal",
    },
]


def map_news_keywords(title: str, summary: str = "") -> dict[str, str]:
    text = f"{title or ''} {summary or ''}".lower()
    matched_keywords = []
    for rule in KEYWORD_RULES:
        hits = [keyword for keyword in rule["keywords"] if keyword in text]
        if hits:
            matched_keywords.extend(hits)
            return {
                "detected_keywords": ",".join(dict.fromkeys(matched_keywords)),
                "detected_layer": rule["layer"],
                "detected_category": rule["category"],
                "event_type": rule["event_type"],
            }

    return {
        "detected_keywords": "",
        "detected_layer": "",
        "detected_category": "",
        "event_type": "",
    }
