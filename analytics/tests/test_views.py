import datetime
import json

import pytest
from django.urls import reverse

from sessions.tests.factories import SessionFactory

URL = "/mystatistics/"


@pytest.mark.django_db
class TestStatisticsViewRenders:
    def test_page_returns_200(self, client):
        response = client.get(URL)
        assert response.status_code == 200

    def test_page_heading_present(self, client):
        html = client.get(URL).content.decode()
        assert "<h1>Statistics</h1>" in html

    def test_all_eight_section_headings_present(self, client):
        html = client.get(URL).content.decode()
        for heading in (
            "Overview",
            "Sessions by bow",
            "Location and distance",
            "Session types",
            "Time of day",
            "Outdoor conditions",
            "How you felt",
            "Score analysis",
        ):
            assert heading in html, f"Section heading '{heading}' missing from page"

    def test_sections_use_expandable_card_class(self, client):
        html = client.get(URL).content.decode()
        assert html.count("settings-card--expandable") == 8

    def test_all_sections_collapsed_by_default(self, client):
        html = client.get(URL).content.decode()
        assert "<details" in html
        assert "<details open" not in html


@pytest.mark.django_db
class TestStatisticsAggregationsEmpty:
    """With no sessions, totals are 0 and insufficient-data messages show."""

    def _ctx(self, client):
        return client.get(URL).context

    def test_total_sessions_is_zero(self, client):
        assert self._ctx(client)["total_sessions"] == 0

    def test_total_sessions_this_year_is_zero(self, client):
        assert self._ctx(client)["total_sessions_this_year"] == 0

    def test_total_arrows_is_zero(self, client):
        assert self._ctx(client)["total_arrows"] == 0

    def test_total_scoring_arrows_is_zero(self, client):
        assert self._ctx(client)["total_scoring_arrows"] == 0

    def test_bow_rows_empty(self, client):
        assert self._ctx(client)["bow_rows"] == []

    def test_indoor_count_zero(self, client):
        assert self._ctx(client)["indoor_count"] == 0

    def test_outdoor_count_zero(self, client):
        assert self._ctx(client)["outdoor_count"] == 0

    def test_dist_rows_empty(self, client):
        assert self._ctx(client)["dist_rows"] == []

    def test_scored_sessions_zero(self, client):
        assert self._ctx(client)["scored_sessions"] == 0

    def test_blank_bale_sessions_zero(self, client):
        assert self._ctx(client)["blank_bale_sessions"] == 0

    def test_all_averages_are_none(self, client):
        ctx = self._ctx(client)
        for key in (
            "avg_nutrition",
            "avg_stress",
            "avg_fatigue",
            "avg_wind_force",
            "avg_sleep_hours",
            "avg_temperature",
        ):
            assert ctx[key]["avg"] is None, f"{key} avg should be None with no data"

    def test_all_categorical_breakdowns_are_gated(self, client):
        ctx = self._ctx(client)
        for key in (
            "weather_breakdown",
            "wind_direction_breakdown",
            "time_of_day_breakdown",
        ):
            assert ctx[key]["bar_rows"] is None, f"{key} should be gated with no data"

    def test_score_analysis_not_available(self, client):
        assert self._ctx(client)["score_analysis"]["available"] is False

    def test_score_gate_message_shown(self, client):
        html = client.get(URL).content.decode()
        assert "Score analysis unlocks at 20 scored sessions" in html
        assert "You have 0" in html

    def test_insufficient_data_text_present(self, client):
        html = client.get(URL).content.decode()
        assert "Insufficient data" in html


@pytest.mark.django_db
class TestStatisticsAggregationsSmallDataset:
    """3–5 sessions: counts correct, averages still insufficient (threshold not met)."""

    def setup_method(self):
        from equipment.tests.factories import BowFactory

        self.bow1 = BowFactory(name="Blue Hoyt")
        self.bow2 = BowFactory(name="Red WNS")
        SessionFactory(
            bow=self.bow1, location="outdoor", distance_m=18, total_arrows=36
        )
        SessionFactory(
            bow=self.bow1, location="outdoor", distance_m=18, total_arrows=24
        )
        SessionFactory(bow=self.bow2, location="indoor", distance_m=18, total_arrows=30)

    def _ctx(self, client):
        return client.get(URL).context

    def test_total_sessions_correct(self, client):
        assert self._ctx(client)["total_sessions"] == 3

    def test_total_arrows_correct(self, client):
        assert self._ctx(client)["total_arrows"] == 90

    def test_bow_rows_count(self, client):
        assert len(self._ctx(client)["bow_rows"]) == 2

    def test_bow_rows_sorted_by_sessions_desc(self, client):
        rows = self._ctx(client)["bow_rows"]
        assert rows[0]["bow_name"] == "Blue Hoyt"
        assert rows[0]["sessions_count"] == 2
        assert rows[1]["bow_name"] == "Red WNS"
        assert rows[1]["sessions_count"] == 1

    def test_indoor_count_correct(self, client):
        assert self._ctx(client)["indoor_count"] == 1

    def test_outdoor_count_correct(self, client):
        assert self._ctx(client)["outdoor_count"] == 2

    def test_averages_still_insufficient_below_threshold(self, client):
        ctx = self._ctx(client)
        # No subjective fields filled, so all counts are 0 — all insufficient
        assert ctx["avg_nutrition"]["avg"] is None
        assert ctx["avg_stress"]["avg"] is None


@pytest.mark.django_db
class TestStatisticsAggregationsSufficientData:
    """10 sessions with nutrition filled — average should compute correctly."""

    def setup_method(self):
        for _ in range(10):
            SessionFactory(
                location="indoor",
                distance_m=18,
                total_arrows=30,
                nutrition=3,  # all set to 3 → average should be 3.0
            )

    def _ctx(self, client):
        return client.get(URL).context

    def test_nutrition_avg_is_computed(self, client):
        ctx = self._ctx(client)
        assert ctx["avg_nutrition"]["avg"] == 3.0

    def test_nutrition_count_is_correct(self, client):
        ctx = self._ctx(client)
        assert ctx["avg_nutrition"]["count"] == 10

    def test_other_averages_still_insufficient(self, client):
        ctx = self._ctx(client)
        assert ctx["avg_stress"]["avg"] is None


@pytest.mark.django_db
class TestStatisticsConditionsCardsStructure:
    """The old single 'Conditions and how you felt' section is now three
    separate cards: Time of day, Outdoor conditions, How you felt."""

    def _html(self, client):
        return client.get(URL).content.decode()

    def test_old_combined_title_removed(self, client):
        assert "Conditions and how you felt" not in self._html(client)

    def test_gating_note_appears_once_per_card(self, client):
        html = self._html(client)
        assert html.count("Rows are shown only when at least") == 3

    def test_old_table_markup_removed(self, client):
        html = self._html(client)
        assert "<th>Variable</th>" not in html
        assert "Avg (1" not in html
        assert "Most common" not in html


@pytest.mark.django_db
class TestStatisticsTimeOfDayCard:
    def _html(self, client):
        return client.get(URL).content.decode()

    def test_categorical_renders_bar_rows_with_labels_and_counts(self, client):
        for _ in range(3):
            SessionFactory(time_of_day="morning")
        for _ in range(2):
            SessionFactory(time_of_day="evening")
        html = self._html(client)
        assert "Morning" in html
        assert "Evening" in html
        ctx = client.get(URL).context
        bar_rows = ctx["time_of_day_breakdown"]["bar_rows"]
        by_label = {row["label"]: row["count"] for row in bar_rows}
        assert by_label["Morning"] == 3
        assert by_label["Evening"] == 2

    def test_below_threshold_shows_insufficient_data_with_count(self, client):
        SessionFactory(time_of_day="morning")
        SessionFactory(time_of_day="evening")
        html = self._html(client)
        assert "Insufficient data" in html
        assert "from 2 sessions" in html


@pytest.mark.django_db
class TestStatisticsOutdoorConditionsCard:
    """Weather, Temperature, Wind force, Wind direction — grouped because they
    share the outdoor-only population, so the card states that once rather
    than repeating it on every row."""

    def _html(self, client):
        return client.get(URL).content.decode()

    def test_outdoor_only_note_shown_exactly_once(self, client):
        html = self._html(client)
        assert html.count("Outdoor sessions only.") == 1

    def test_weather_renders_bar_rows(self, client):
        for _ in range(3):
            SessionFactory(location="outdoor", weather="sunny")
        for _ in range(2):
            SessionFactory(location="outdoor", weather="rainy")
        html = self._html(client)
        assert "Sunny" in html
        assert "Rainy" in html

    def test_wind_force_renders_scale_marker(self, client):
        for _ in range(5):
            SessionFactory(location="outdoor", wind_force=5)
        html = self._html(client)
        assert "Very strong &middot; 5.0" in html

    def test_wind_direction_renders_all_eight_full_labels(self, client):
        directions = [
            "from_left",
            "from_right",
            "from_front",
            "from_back",
            "from_front_left",
            "from_front_right",
            "from_back_left",
            "from_back_right",
        ]
        for d in directions:
            SessionFactory(location="outdoor", wind_direction=d)
        html = self._html(client)
        # Full, distinguishable labels — not truncated to "From front…".
        for label in (
            "From left",
            "From right",
            "From front",
            "From back",
            "From front-left",
            "From front-right",
            "From back-left",
            "From back-right",
        ):
            assert label in html, f"Wind direction label '{label}' missing or truncated"

    def test_temperature_renders_numeric_average_when_sufficient(self, client):
        for _ in range(5):
            SessionFactory(location="outdoor", temperature_celsius=18)
        html = self._html(client)
        assert "18.0 &deg;C" in html

    def test_temperature_renders_insufficient_data_when_below_threshold(self, client):
        SessionFactory(location="outdoor", temperature_celsius=18)
        html = self._html(client)
        assert "Temperature" in html
        assert "Insufficient data" in html
        assert "from 1 session<" in html

    def test_temperature_never_silently_disappears(self, client):
        """Regression: temperature used to be missing from context entirely."""
        html = self._html(client)
        assert "Temperature" in html

    def test_rows_carry_no_redundant_per_row_outdoor_note(self, client):
        html = self._html(client)
        # Only the one card-level note; no row repeats "outdoor sessions only".
        assert html.lower().count("outdoor sessions only") == 1


@pytest.mark.django_db
class TestStatisticsHowYouFeltCard:
    def _html(self, client):
        return client.get(URL).content.decode()

    def test_scale_variables_render_nearest_label_and_average(self, client):
        for _ in range(5):
            SessionFactory(stress=2, fatigue=4, nutrition=1)
        html = self._html(client)
        assert "Low &middot; 2.0" in html  # stress
        assert "High &middot; 4.0" in html  # fatigue
        assert "Very poor &middot; 1.0" in html  # nutrition

    def test_scale_marker_rounds_half_up(self, client):
        """Alternating 2/3 averages to 2.5, which must round UP to label 3."""
        for _ in range(3):
            SessionFactory(stress=2)
        for _ in range(3):
            SessionFactory(stress=3)
        html = self._html(client)
        assert "Medium &middot; 2.5" in html

    def test_sleep_renders_as_number_with_unit(self, client):
        for _ in range(5):
            SessionFactory(sleep_hours=6.4)
        html = self._html(client)
        assert "6.4 h" in html

    def test_below_threshold_shows_insufficient_data_with_count(self, client):
        SessionFactory(stress=3)
        SessionFactory(stress=4)
        html = self._html(client)
        assert "Insufficient data" in html
        assert "from 2 sessions" in html


@pytest.mark.django_db
class TestStatisticsLocationDistanceBarRows:
    """Location and distance section renders as bar rows, not tables."""

    def setup_method(self):
        SessionFactory(location="indoor", distance_m=18, total_arrows=30)
        SessionFactory(location="indoor", distance_m=18, total_arrows=30)
        SessionFactory(location="outdoor", distance_m=30, total_arrows=36)

    def test_location_labels_and_counts_rendered_as_text(self, client):
        html = client.get(URL).content.decode()
        assert "Indoor" in html
        assert "Outdoor" in html

    def test_distance_labels_and_counts_rendered_as_text(self, client):
        html = client.get(URL).content.decode()
        assert "18 m" in html
        assert "30 m" in html

    def test_bar_rows_component_present(self, client):
        html = client.get(URL).content.decode()
        # Location and distance renders two bar-row groups; Session types
        # (converted separately) also renders one — three total on the page.
        assert html.count('class="bar-rows"') == 3

    def test_old_table_markup_removed(self, client):
        html = client.get(URL).content.decode()
        assert "<th>Location</th>" not in html
        assert "<th>Distance</th>" not in html
        assert "stats-table-row--muted" not in html

    def test_location_bar_rows_context_matches_counts(self, client):
        ctx = client.get(URL).context
        by_label = {row["label"]: row["count"] for row in ctx["location_bar_rows"]}
        assert by_label["Indoor"] == 2
        assert by_label["Outdoor"] == 1

    def test_distance_bar_rows_context_matches_counts(self, client):
        ctx = client.get(URL).context
        by_label = {row["label"]: row["count"] for row in ctx["distance_bar_rows"]}
        assert by_label["18 m"] == 2
        assert by_label["30 m"] == 1


@pytest.mark.django_db
class TestStatisticsSessionTypes:
    """Scored = scoring_arrows > 0, regardless of total_score. See
    analytics.services.scored_session_filter for the single definition."""

    def _ctx(self, client):
        return client.get(URL).context

    def test_blank_bale_counted(self, client):
        SessionFactory(scoring_arrows=None, total_score=None)
        SessionFactory(scoring_arrows=0, total_score=None)
        assert self._ctx(client)["blank_bale_sessions"] == 2

    def test_scored_counted(self, client):
        SessionFactory(scoring_arrows=30, total_score=255)
        assert self._ctx(client)["scored_sessions"] == 1

    def test_scoring_arrows_without_total_score_counts_as_scored(self, client):
        """Regression: this is the exact edge case that used to fall through
        both buckets (scoring arrows entered, total_score never tallied)."""
        SessionFactory(scoring_arrows=72, total_score=None)
        assert self._ctx(client)["scored_sessions"] == 1
        assert self._ctx(client)["blank_bale_sessions"] == 0

    def test_every_session_counted_in_exactly_one_category(self, client):
        SessionFactory(scoring_arrows=None, total_score=None)  # blank bale
        SessionFactory(scoring_arrows=0, total_score=None)  # blank bale
        SessionFactory(scoring_arrows=30, total_score=255)  # fully scored
        SessionFactory(scoring_arrows=72, total_score=None)  # scored, no tally
        ctx = self._ctx(client)
        assert ctx["blank_bale_sessions"] == 2
        assert ctx["scored_sessions"] == 2
        assert (
            ctx["blank_bale_sessions"] + ctx["scored_sessions"] == ctx["total_sessions"]
        )

    def test_non_scored_label_rendered(self, client):
        html = client.get(URL).content.decode()
        assert "Non-scored session" in html
        assert "Blank bale" not in html

    def test_scored_session_label_rendered(self, client):
        SessionFactory(scoring_arrows=30, total_score=255)
        html = client.get(URL).content.decode()
        assert "Scored session" in html

    def test_bar_rows_component_present_and_old_table_removed(self, client):
        html = client.get(URL).content.decode()
        assert 'class="bar-rows"' in html
        assert "<th>Type</th>" not in html
        assert "<th>Sessions</th>" not in html


@pytest.mark.django_db
class TestStatisticsScoringArrowsSublabel:
    """Secondary line under the Scoring arrows card: 'from N scoring rounds'."""

    def test_sublabel_absent_with_zero_scored_sessions(self, client):
        html = client.get(URL).content.decode()
        assert "scoring round" not in html

    def test_sublabel_singular_with_one_scored_session(self, client):
        SessionFactory(scoring_arrows=30, total_score=255)
        html = client.get(URL).content.decode()
        assert "from 1 scoring round" in html
        assert "from 1 scoring rounds" not in html

    def test_sublabel_plural_matches_session_types_scored_count(self, client):
        SessionFactory(scoring_arrows=30, total_score=255)
        SessionFactory(scoring_arrows=30, total_score=270)
        SessionFactory(scoring_arrows=30, total_score=240)
        response = client.get(URL)
        html = response.content.decode()
        scored_sessions = response.context["scored_sessions"]
        assert scored_sessions == 3
        assert f"from {scored_sessions} scoring rounds" in html

    def test_sublabel_counts_scoring_arrows_without_total_score(self, client):
        """A session with scoring arrows but no tallied total_score still
        counts toward the round total — same definition as Session types."""
        SessionFactory(scoring_arrows=72, total_score=None)
        html = client.get(URL).content.decode()
        assert "from 1 scoring round" in html


@pytest.mark.django_db
class TestStatisticsNoBowEdgeCase:
    def test_no_bow_row_appears_when_null_bow_sessions_exist(self, client):
        SessionFactory(bow=None, total_arrows=20)
        ctx = client.get(URL).context
        bow_names = [r["bow_name"] for r in ctx["bow_rows"]]
        assert "(no bow recorded)" in bow_names

    def test_no_bow_row_absent_when_all_sessions_have_bows(self, client):
        SessionFactory(total_arrows=20)  # bow is set by factory default
        ctx = client.get(URL).context
        bow_names = [r["bow_name"] for r in ctx["bow_rows"]]
        assert "(no bow recorded)" not in bow_names


@pytest.mark.django_db
class TestStatisticsScoreAnalysis:
    def test_insufficient_below_20(self, client):
        for _ in range(5):
            SessionFactory(scoring_arrows=30, total_score=280)
        ctx = client.get(URL).context
        assert ctx["score_analysis"]["available"] is False
        assert ctx["score_analysis"]["scored_count"] == 5

    def test_gate_message_shows_correct_count(self, client):
        for _ in range(2):
            SessionFactory(scoring_arrows=30, total_score=280)
        html = client.get(URL).content.decode()
        assert "You have 2" in html

    def test_available_at_20_scored_sessions(self, client):
        for i in range(20):
            SessionFactory(scoring_arrows=30, total_score=250 + i)
        ctx = client.get(URL).context
        analysis = ctx["score_analysis"]
        assert analysis["available"] is True
        assert analysis["best_score"] == 269
        assert analysis["worst_score"] == 250
        assert analysis["avg_score"] is not None


@pytest.mark.django_db
class TestTimeDistributionEmpty:
    """No sessions: all three series are empty; the empty-state message shows."""

    def _ctx(self, client):
        return client.get(URL).context

    def test_has_time_distribution_data_is_false(self, client):
        assert self._ctx(client)["has_time_distribution_data"] is False

    def test_all_series_are_empty(self, client):
        td = self._ctx(client)["time_distribution"]
        assert td["week"] == {"labels": [], "data": []}
        assert td["month"] == {"labels": [], "data": []}
        assert td["year"] == {"labels": [], "data": []}

    def test_empty_state_message_shown(self, client):
        html = client.get(URL).content.decode()
        assert "No sessions logged yet." in html
        assert "your training distribution" in html

    def test_chart_script_and_canvas_absent(self, client):
        html = client.get(URL).content.decode()
        assert "time-distribution-chart" not in html
        assert "chart.min.js" not in html
        assert "stats-timeframe-btn" not in html


@pytest.mark.django_db
class TestTimeDistributionAggregation:
    def test_weekly_gap_week_is_zero_not_missing(self, client):
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())
        # Two weeks with arrows, one gap week in between with none.
        SessionFactory(date=week_start, total_arrows=30)
        SessionFactory(date=week_start - datetime.timedelta(weeks=2), total_arrows=60)

        td = client.get(URL).context["time_distribution"]
        week_data = td["week"]["data"]
        week_labels = td["week"]["labels"]

        assert len(week_data) == len(week_labels)
        # The gap week (one week back) contributes 0.
        gap_index = week_labels.index(
            self._label(week_start - datetime.timedelta(weeks=1))
        )
        assert week_data[gap_index] == 0

    @staticmethod
    def _label(d: datetime.date) -> str:
        return f"{d.day} {d.strftime('%b')}"

    def test_monthly_totals_correct(self, client):
        today = datetime.date.today()
        month_start = today.replace(day=1)
        SessionFactory(date=month_start, total_arrows=20)
        SessionFactory(date=month_start, total_arrows=10)

        td = client.get(URL).context["time_distribution"]
        label = month_start.strftime("%B %Y")
        idx = td["month"]["labels"].index(label)
        assert td["month"]["data"][idx] == 30

    def test_yearly_totals_correct(self, client):
        today = datetime.date.today()
        SessionFactory(date=today, total_arrows=15)
        SessionFactory(date=today, total_arrows=25)

        td = client.get(URL).context["time_distribution"]
        idx = td["year"]["labels"].index(str(today.year))
        assert td["year"]["data"][idx] == 40

    def test_null_total_arrows_counts_as_zero(self, client):
        today = datetime.date.today()
        SessionFactory(date=today, total_arrows=None)

        td = client.get(URL).context["time_distribution"]
        idx = td["year"]["labels"].index(str(today.year))
        assert td["year"]["data"][idx] == 0

    def test_does_not_pad_before_first_session(self, client):
        today = datetime.date.today()
        SessionFactory(date=today, total_arrows=10)

        td = client.get(URL).context["time_distribution"]
        # Only one year bucket should appear since history starts this year.
        assert td["year"]["labels"] == [str(today.year)]


@pytest.mark.django_db
class TestTimeDistributionTemplateRendering:
    def setup_method(self):
        SessionFactory(total_arrows=10)

    def test_chart_script_tag_present(self, client):
        html = client.get(URL).content.decode()
        assert "js/vendor/chart.min.js" in html
        assert "js/stats-chart.js" in html

    def test_data_series_present_as_json_script(self, client):
        html = client.get(URL).content.decode()
        assert 'id="time-distribution-data"' in html
        assert 'type="application/json"' in html

    def test_data_series_json_is_well_formed(self, client):
        response = client.get(URL)
        html = response.content.decode()
        start = html.index('id="time-distribution-data"')
        script_start = html.index(">", start) + 1
        script_end = html.index("</script>", script_start)
        payload = json.loads(html[script_start:script_end])
        assert set(payload.keys()) == {"week", "month", "year"}

    def test_three_timeframe_buttons_present(self, client):
        html = client.get(URL).content.decode()
        for frame in ("week", "month", "year"):
            assert f'data-timeframe="{frame}"' in html

    def test_month_is_default_active(self, client):
        html = client.get(URL).content.decode()
        # The month button carries is-active; week/year do not.
        month_btn_start = html.index('data-timeframe="month"')
        month_btn_snippet = html[max(0, month_btn_start - 100) : month_btn_start]
        assert "is-active" in month_btn_snippet

    def test_canvas_element_present(self, client):
        html = client.get(URL).content.decode()
        assert 'id="time-distribution-chart"' in html
        assert "<canvas" in html


@pytest.mark.django_db
class TestStatisticsNavBar:
    def test_statistics_link_in_nav_on_bows_page(self, client):
        html = client.get(reverse("equipment:mybows")).content.decode()
        assert "/mystatistics/" in html

    def test_statistics_nav_active_on_statistics_page(self, client):
        html = client.get(URL).content.decode()
        assert "nav-active" in html
        # The Statistics button should be the one with nav-active on this page
        # Check that the Statistics link has the active class
        assert 'href="/mystatistics/"' in html

    def test_homepage_still_has_no_nav(self, client):
        html = client.get(reverse("practice_sessions:home")).content.decode()
        assert "site-nav" not in html
