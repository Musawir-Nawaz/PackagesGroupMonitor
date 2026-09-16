import re
from functools import lru_cache

from transformers import pipeline

# Open-source, runs locally, no paid AI API (spec section 8). This model
# only outputs positive/neutral/negative — "mixed" isn't a native class, so
# it's derived below by splitting on contrastive conjunctions and checking
# whether opposing clauses both score strongly.
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

CONTRAST_SPLIT = re.compile(r"\b(but|however|although|though|yet)\b", re.IGNORECASE)
CONTRAST_WORDS = {"but", "however", "although", "though", "yet"}
STRONG_THRESHOLD = 0.6


@lru_cache(maxsize=1)
def _get_pipeline():
    return pipeline("sentiment-analysis", model=MODEL_NAME, tokenizer=MODEL_NAME)


def _classify_clause(clause: str) -> tuple[str, float]:
    result = _get_pipeline()(clause, truncation=True)[0]
    return result["label"].lower(), float(result["score"])


def analyze_sentiment(text: str) -> dict:
    text = text.strip()
    if not text:
        return {"sentiment": "neutral", "confidence": 1.0}

    parts = [p.strip() for p in CONTRAST_SPLIT.split(text)]
    clauses = [p for p in parts if p and p.lower() not in CONTRAST_WORDS]

    if len(clauses) >= 2:
        clause_results = [_classify_clause(c) for c in clauses]
        positive_scores = [s for label, s in clause_results if label == "positive" and s >= STRONG_THRESHOLD]
        negative_scores = [s for label, s in clause_results if label == "negative" and s >= STRONG_THRESHOLD]
        if positive_scores and negative_scores:
            confidence = round((max(positive_scores) + max(negative_scores)) / 2, 4)
            return {"sentiment": "mixed", "confidence": confidence}

    label, score = _classify_clause(text)
    return {"sentiment": label, "confidence": round(score, 4)}
