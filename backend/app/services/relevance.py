import re

from app.config import settings

_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")
_EXTRA_SPACES = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Lowercase and fold punctuation/underscores/hyphens to spaces, so
    "Packages-Mall", "Packages_Mall" and "Packages   Mall" all reduce to
    the same "packages mall" a plain keyword match can find."""
    folded = _NON_ALNUM.sub(" ", text.lower())
    return _EXTRA_SPACES.sub(" ", folded).strip()


def is_relevant(text: str, keywords: list[str] | None = None) -> bool:
    """Keyword-match relevance filter (spec section 7).

    Keywords come from the configurable RELEVANCE_KEYWORDS env var, not
    hard-coded, so the list can be edited without a code change — that list
    already includes common short forms (e.g. "Packages Ltd", "Pkgs Mall")
    alongside the full names, deliberately excluding bare 2-3 letter
    acronyms ("PM", "PG") since those false-positive too heavily on
    unrelated social media chatter to be usable.

    Matching is done on normalized text so punctuation/spacing variants
    (hyphens, underscores, run-together hashtags like "#PackagesMall")
    still match a spaced-out keyword without needing every combination
    spelled out in the keyword list.
    """
    keywords = keywords if keywords is not None else settings.relevance_keyword_list
    text_normalized = _normalize(text)
    text_compact = text_normalized.replace(" ", "")

    for keyword in keywords:
        keyword_normalized = _normalize(keyword)
        if keyword_normalized in text_normalized:
            return True
        if keyword_normalized.replace(" ", "") in text_compact:
            return True
    return False
