import datetime

from django.db.models import Avg, Count, Max, Min, Sum
from django.db.models.functions import Coalesce, TruncMonth, TruncWeek, TruncYear
from django.utils import timezone
from django.views.generic import TemplateView

from analytics.services import build_bar_rows, build_scale_marker, scored_session_filter
from sessions.models import Session

_SUBJECTIVE_MIN_N = 5
_SCORE_MIN_N = 20
_WEEKS_SHOWN = 12
_MONTHS_SHOWN = 12
_YEARS_SHOWN = 5


def _week_start(d: datetime.date) -> datetime.date:
    """Return the Monday of the week containing d (matches Django's TruncWeek)."""
    return d - datetime.timedelta(days=d.weekday())


def _month_start(d: datetime.date) -> datetime.date:
    return d.replace(day=1)


def _shift_month(d: datetime.date, delta: int) -> datetime.date:
    """Return the first-of-month `delta` months away from d's month."""
    zero_based = d.month - 1 + delta
    year = d.year + zero_based // 12
    month = zero_based % 12 + 1
    return datetime.date(year, month, 1)


def _time_distribution(qs, earliest_date: datetime.date | None) -> dict:
    """Compute Week/Month/Year arrow-count series, including zero-arrow gap periods.

    Periods before the archer's first-ever session are never padded in.
    """
    if earliest_date is None:
        return {
            "week": {"labels": [], "data": []},
            "month": {"labels": [], "data": []},
            "year": {"labels": [], "data": []},
        }

    today = timezone.localdate()

    # --- Weekly ---
    current_week_start = _week_start(today)
    week_starts = [
        current_week_start - datetime.timedelta(weeks=i)
        for i in range(_WEEKS_SHOWN - 1, -1, -1)
    ]
    earliest_week_start = _week_start(earliest_date)
    week_starts = [w for w in week_starts if w >= earliest_week_start]
    weekly_totals = {
        row["period"]: row["total"]
        for row in (
            qs.annotate(period=TruncWeek("date"))
            .values("period")
            .annotate(total=Coalesce(Sum("total_arrows"), 0))
        )
    }
    week_series = {
        "labels": [f"{w.day} {w.strftime('%b')}" for w in week_starts],
        "data": [weekly_totals.get(w, 0) for w in week_starts],
    }

    # --- Monthly ---
    current_month_start = _month_start(today)
    month_starts = [
        _shift_month(current_month_start, -i) for i in range(_MONTHS_SHOWN - 1, -1, -1)
    ]
    earliest_month_start = _month_start(earliest_date)
    month_starts = [m for m in month_starts if m >= earliest_month_start]
    monthly_totals = {
        row["period"]: row["total"]
        for row in (
            qs.annotate(period=TruncMonth("date"))
            .values("period")
            .annotate(total=Coalesce(Sum("total_arrows"), 0))
        )
    }
    month_series = {
        "labels": [m.strftime("%B %Y") for m in month_starts],
        "data": [monthly_totals.get(m, 0) for m in month_starts],
    }

    # --- Yearly ---
    years = [today.year - i for i in range(_YEARS_SHOWN - 1, -1, -1)]
    years = [y for y in years if y >= earliest_date.year]
    yearly_totals = {
        row["period"].year: row["total"]
        for row in (
            qs.annotate(period=TruncYear("date"))
            .values("period")
            .annotate(total=Coalesce(Sum("total_arrows"), 0))
        )
    }
    year_series = {
        "labels": [str(y) for y in years],
        "data": [yearly_totals.get(y, 0) for y in years],
    }

    return {"week": week_series, "month": month_series, "year": year_series}


def _avg_or_none(qs, field: str) -> dict:
    """Return {"avg": rounded_float, "count": n} or {"avg": None, "count": n}."""
    result = qs.filter(**{f"{field}__isnull": False}).aggregate(
        count=Count("pk"),
        avg=Avg(field),
    )
    count = result["count"]
    avg = round(result["avg"], 1) if result["avg"] is not None else None
    return {"avg": avg if count >= _SUBJECTIVE_MIN_N else None, "count": count}


def _category_breakdown_or_none(qs, field: str, choices: list) -> dict:
    """Return {"bar_rows": [...], "count": n} or {"bar_rows": None, "count": n}.

    `bar_rows` covers every choice value in its declared order (zero-count
    categories included, via build_bar_rows), gated at the same minimum-N
    threshold as the averages above. `count` is the total non-null, non-blank
    logged value count, shown even when bar_rows is None so the archer can
    see how far away the threshold is.
    """
    counts = dict(
        qs.filter(**{f"{field}__isnull": False})
        .exclude(**{field: ""})
        .values(field)
        .annotate(count=Count("pk"))
        .values_list(field, "count")
    )
    total = sum(counts.values())
    if total < _SUBJECTIVE_MIN_N:
        return {"bar_rows": None, "count": total}
    pairs = [(label, counts.get(value, 0)) for value, label in choices]
    return {"bar_rows": build_bar_rows(pairs), "count": total}


def _marker_or_none(avg_result: dict, labels: list[str]) -> dict | None:
    """Wrap _avg_or_none's result as a build_scale_marker dict, or None if gated."""
    if avg_result["avg"] is None:
        return None
    return build_scale_marker(avg_result["avg"], labels)


class StatisticsView(TemplateView):
    """Read-only dashboard of aggregated session statistics."""

    template_name = "analytics/mystatistics.html"

    def get_context_data(self, **kwargs: object) -> dict:
        ctx = super().get_context_data(**kwargs)
        qs = Session.objects.all()
        current_year = timezone.localdate().year

        # --- Totals ---
        totals = qs.aggregate(
            total_sessions=Count("pk"),
            total_arrows=Coalesce(Sum("total_arrows"), 0),
            total_scoring_arrows=Coalesce(Sum("scoring_arrows"), 0),
        )
        ctx["total_sessions"] = totals["total_sessions"]
        ctx["total_sessions_this_year"] = qs.filter(date__year=current_year).count()
        ctx["total_arrows"] = totals["total_arrows"]
        ctx["total_scoring_arrows"] = totals["total_scoring_arrows"]
        ctx["total_non_scoring_arrows"] = (
            totals["total_arrows"] - totals["total_scoring_arrows"]
        )

        # --- Time distribution (Overview chart) ---
        earliest_date = qs.aggregate(earliest=Min("date"))["earliest"]
        ctx["time_distribution"] = _time_distribution(qs, earliest_date)
        ctx["has_time_distribution_data"] = totals["total_sessions"] > 0

        # --- Sessions by bow ---
        raw_bow = list(
            qs.values("bow__name")
            .annotate(
                sessions_count=Count("pk"),
                arrows_count=Coalesce(Sum("total_arrows"), 0),
            )
            .order_by("-sessions_count")
        )
        # Separate null-bow rows before mutating keys
        null_bow_entries = [r for r in raw_bow if r["bow__name"] is None]
        bow_rows = sorted(
            [
                {
                    "bow_name": r["bow__name"],
                    "sessions_count": r["sessions_count"],
                    "arrows_count": r["arrows_count"],
                }
                for r in raw_bow
                if r["bow__name"] is not None
            ],
            key=lambda r: -r["sessions_count"],
        )
        if null_bow_entries:
            bow_rows.append(
                {
                    "bow_name": "(no bow recorded)",
                    "sessions_count": null_bow_entries[0]["sessions_count"],
                    "arrows_count": null_bow_entries[0]["arrows_count"],
                }
            )
        ctx["bow_rows"] = bow_rows

        # --- Sessions by location ---
        location_counts = {
            r["location"]: r["count"]
            for r in qs.values("location").annotate(count=Count("pk"))
        }
        ctx["indoor_count"] = location_counts.get(Session.Location.INDOOR, 0)
        ctx["outdoor_count"] = location_counts.get(Session.Location.OUTDOOR, 0)
        ctx["location_not_recorded"] = location_counts.get(
            None, location_counts.get("", 0)
        )
        location_pairs = [
            ("Indoor", ctx["indoor_count"]),
            ("Outdoor", ctx["outdoor_count"]),
        ]
        if ctx["location_not_recorded"]:
            location_pairs.append(("(not recorded)", ctx["location_not_recorded"]))
        ctx["location_bar_rows"] = build_bar_rows(location_pairs)

        # --- Sessions by distance ---
        raw_dist = list(
            qs.values("distance_m")
            .annotate(sessions_count=Count("pk"))
            .order_by("distance_m")
        )
        dist_rows = [r for r in raw_dist if r["distance_m"] is not None]
        null_dist = [r for r in raw_dist if r["distance_m"] is None]
        if null_dist:
            dist_rows.append(
                {
                    "distance_m": None,
                    "sessions_count": null_dist[0]["sessions_count"],
                }
            )
        ctx["dist_rows"] = dist_rows
        distance_pairs = [
            (
                f"{row['distance_m']} m"
                if row["distance_m"] is not None
                else "(not recorded)",
                row["sessions_count"],
            )
            for row in dist_rows
        ]
        ctx["distance_bar_rows"] = build_bar_rows(distance_pairs)

        # --- Session types ---
        # Single definition of "scored" lives in scored_session_filter(); "non-scored"
        # is its exact complement via .exclude(), so every session lands in exactly one
        # bucket. Reused below for the Scoring arrows card and Score analysis gating.
        scored_sessions = qs.filter(scored_session_filter()).count()
        blank_bale_sessions = qs.exclude(scored_session_filter()).count()
        ctx["scored_sessions"] = scored_sessions
        ctx["blank_bale_sessions"] = blank_bale_sessions
        ctx["session_type_bar_rows"] = build_bar_rows(
            [
                ("Non-scored session", blank_bale_sessions),
                ("Scored session", scored_sessions),
            ]
        )

        # --- Subjective variable averages ---
        ctx["avg_nutrition"] = _avg_or_none(qs, "nutrition")
        ctx["avg_stress"] = _avg_or_none(qs, "stress")
        ctx["avg_fatigue"] = _avg_or_none(qs, "fatigue")
        ctx["avg_wind_force"] = _avg_or_none(qs, "wind_force")
        ctx["avg_sleep_hours"] = _avg_or_none(qs, "sleep_hours")
        ctx["avg_temperature"] = _avg_or_none(qs, "temperature_celsius")

        # --- Scale markers (position on a 1-5 scale, not a quantity) ---
        ctx["marker_nutrition"] = _marker_or_none(
            ctx["avg_nutrition"], Session.Nutrition.labels
        )
        ctx["marker_stress"] = _marker_or_none(ctx["avg_stress"], Session.Stress.labels)
        ctx["marker_fatigue"] = _marker_or_none(
            ctx["avg_fatigue"], Session.Fatigue.labels
        )
        ctx["marker_wind_force"] = _marker_or_none(
            ctx["avg_wind_force"], Session.WindForce.labels
        )

        # --- Categorical breakdowns (bar rows, one group per variable) ---
        ctx["weather_breakdown"] = _category_breakdown_or_none(
            qs, "weather", Session.Weather.choices
        )
        ctx["wind_direction_breakdown"] = _category_breakdown_or_none(
            qs, "wind_direction", Session.WindDirection.choices
        )
        ctx["time_of_day_breakdown"] = _category_breakdown_or_none(
            qs, "time_of_day", Session.TimeOfDay.choices
        )

        ctx["subjective_min_n"] = _SUBJECTIVE_MIN_N

        # --- Score analysis ---
        ctx["score_min_n"] = _SCORE_MIN_N
        if scored_sessions >= _SCORE_MIN_N:
            score_qs = qs.filter(scored_session_filter(), total_score__isnull=False)
            score_stats = score_qs.aggregate(
                avg_score=Avg("total_score"),
                best_score=Max("total_score"),
                worst_score=Min("total_score"),
            )
            ctx["score_analysis"] = {
                "available": True,
                "avg_score": (
                    round(score_stats["avg_score"], 1)
                    if score_stats["avg_score"]
                    else None
                ),
                "best_score": score_stats["best_score"],
                "worst_score": score_stats["worst_score"],
            }
        else:
            ctx["score_analysis"] = {
                "available": False,
                "scored_count": scored_sessions,
            }

        return ctx
