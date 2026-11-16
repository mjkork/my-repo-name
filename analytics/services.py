"""Reusable presentation helpers for the Statistics page."""


def build_bar_rows(pairs: list[tuple[str, int]]) -> list[dict]:
    """Turn (label, count) pairs into rows for the bar-row template component.

    Each row dict has:
    - `label` — the pair's label, unchanged.
    - `count` — the pair's count, unchanged.
    - `percent` — count as a whole-number percentage of the sum of all counts.
    - `width` — bar width as a whole-number percentage of the largest count
      in the group (the largest bar is 100%). A non-zero count that would
      round below 2 is floored to 2 so the bar stays visible; a zero count
      is always width 0.
    """
    total = sum(count for _, count in pairs)
    max_count = max((count for _, count in pairs), default=0)

    rows = []
    for label, count in pairs:
        percent = round(count / total * 100) if total else 0
        if count == 0 or max_count == 0:
            width = 0
        else:
            width = max(round(count / max_count * 100), 2)
        rows.append({"label": label, "count": count, "percent": percent, "width": width})
    return rows
