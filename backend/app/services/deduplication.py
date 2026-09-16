def compute_dedup_key(item: dict) -> str:
    """Deterministic identity for a collected item, used as the unique
    constraint that prevents the same post/comment being inserted twice
    across collection runs (spec section 28, point 3)."""
    identifier = item.get("comment_id") or item.get("post_id")
    return f"{item['platform']}:{item['source_type']}:{identifier}"
