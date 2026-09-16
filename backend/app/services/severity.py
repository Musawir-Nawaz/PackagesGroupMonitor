import re

# Not a simple function of sentiment confidence — a comment can be clearly
# negative (high confidence) without being a serious reputation risk (low
# severity), and vice versa (spec section 9).

CRITICAL_KEYWORDS = [
    "scam", "scamming", "scammed", "fraud", "fraudulent", "sue", "suing",
    "lawsuit", "illegal", "cheat", "cheated", "steal", "stealing", "stole",
]

HIGH_KEYWORDS = [
    "nobody is helping", "nobody helped", "no response", "never responds",
    "never respond", "unacceptable", "disgusting", "worst", "terrible",
    "awful", "horrible", "boycott",
]

MODERATE_KEYWORDS = [
    "disappointed", "unhappy", "frustrated", "frustrating", "poor",
    "mediocre", "not good", "not happy", "not satisfied", "annoyed",
]

INTENSIFIERS = ["very", "extremely", "absolutely", "completely", "totally", "really"]


def compute_severity(text: str, confidence: float) -> int:
    """0-100 severity score for a negative/mixed comment."""
    text_lower = text.lower()

    score = round(confidence * 25)  # sentiment strength contributes, but isn't the whole picture

    has_critical = any(kw in text_lower for kw in CRITICAL_KEYWORDS)
    has_high = any(kw in text_lower for kw in HIGH_KEYWORDS)
    has_moderate = any(re.search(rf"\b{re.escape(kw)}\b", text_lower) for kw in MODERATE_KEYWORDS)
    has_intensifier = any(re.search(rf"\b{kw}\b", text_lower) for kw in INTENSIFIERS)

    if has_critical:
        score += 55
    if has_high:
        score += 30
    if has_moderate:
        score += 18
    if has_intensifier and (has_moderate or has_high or has_critical):
        score += 10

    return max(0, min(100, score))


def severity_label(score: int) -> str:
    if score <= 30:
        return "LOW"
    if score <= 60:
        return "MEDIUM"
    if score <= 80:
        return "HIGH"
    return "CRITICAL"
