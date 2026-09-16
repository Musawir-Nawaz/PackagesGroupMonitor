import re

# Ordered so more specific topics are checked before the generic ones they
# could otherwise be swallowed by (e.g. "Packages Mall" before "Complaints").
# Extend by adding a new (topic, keywords) tuple — no other code changes needed.
TOPIC_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Packages Mall", ["packages mall"]),
    ("Sustainability", ["sustainab", "eco-friendly", "eco friendly", "recycl", "green initiative"]),
    ("Corporate Social Responsibility", ["csr", "corporate social responsibility", "community initiative", "charity", "donation"]),
    ("Customer Service", ["customer service", "customer support", "complaint", "complained", "response", "responded", "helpline", "no one helped", "nobody helped", "nobody is helping", "scam", "scamming", "fraud", "cheated"]),
    ("Product Quality", ["product quality", "defective", "quality of the product", "poor quality", "well made", "durable"]),
    ("Pricing", ["price", "pricing", "expensive", "overpriced", "cheap", "cost too much", "affordable"]),
    ("Delivery", ["delivery", "shipping", "shipment", "delayed order", "late delivery"]),
    ("Logistics", ["logistics", "warehouse", "supply chain", "distribution"]),
    ("Packaging", ["packaging material", "packaging quality", "converting business", "carton", "corrugated"]),
    ("Employment", ["hiring", "job opening", "careers page", "recruitment", "apply now", "vacancy"]),
    ("Employees", ["employee", "staff", "workers", "workforce", "hr policy"]),
    ("Management", ["management", "leadership", "ceo", "board of directors", "executives"]),
    ("Advertising", ["advertisement", "advert", "commercial", "campaign", "marketing"]),
    ("Complaints", ["complaint", "complained", "disappointed", "unacceptable"]),
]

DEFAULT_TOPIC = "General"


def classify_topic(text: str) -> str:
    text_lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS:
        if any(re.search(re.escape(kw), text_lower) for kw in keywords):
            return topic
    return DEFAULT_TOPIC
