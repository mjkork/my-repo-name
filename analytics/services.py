"""Reusable presentation helpers for the Statistics page."""

import math

from django.db.models import Q


def scored_session_filter() -> Q:
    """The single definition of a "scored" session: at least one scoring arrow.

    A session is scored if it has any scoring arrows recorded, regardless of
    whether a total_score was ever tallied for it — "scored" means "shot at
    a scored target face," not "has a final number." This is a true complement
    of "non-scored" (no scoring arrows recorded), so every session falls into
    exactly one of the two buckets.
    """
    return Q(scoring_arrows__gt=0)


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
        rows.append(
            {"label": label, "count": count, "percent": percent, "width": width}
        )
    return rows


def build_scale_marker(average: float, labels: list[str]) -> dict:
    """Position-on-scale data for a 1-5 average, given the scale's 5 ordered labels.

    `labels` is the scale's labels in declared order (label for 1 first, label
    for 5 last) — e.g. Session.Stress.labels. Returns:
    - `average` — formatted to one decimal place, e.g. "1.7".
    - `nearest_label` — the label for the average rounded to the nearest integer,
      rounding .5 up (not Python's round-half-to-even).
    - `position` — percent along the track, (average - 1) / 4 * 100.
    - `low_label` / `high_label` — the labels for 1 and 5.

    This marks a *position*, not a quantity — there is no good/bad framing here,
    since scale polarity differs by variable (see PROJECT_NOTES.md).
    """
    nearest_index = math.floor(average + 0.5)
    nearest_index = min(max(nearest_index, 1), 5)
    return {
        "average": f"{average:.1f}",
        "nearest_label": labels[nearest_index - 1],
        "position": round((average - 1) / 4 * 100, 2),
        "low_label": labels[0],
        "high_label": labels[-1],
    }
