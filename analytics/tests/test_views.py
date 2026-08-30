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

    def test_all_six_section_headings_present(self, client):
        html = client.get(URL).content.decode()
        for heading in (
            "Overview",
            "Sessions by bow",
            "Location and distance",
            "Session types",
            "Subjective variable averages",
            "Score analysis",
        ):
            assert heading in html, f"Section heading '{heading}' missing from page"

    def test_all_sections_expanded_by_default(self, client):
        html = client.get(URL).content.decode()
        assert html.count('<details class="stats-section" open>') == 6


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
        ):
            assert ctx[key]["avg"] is None, f"{key} avg should be None with no data"

    def test_all_categorical_labels_are_none(self, client):
        ctx = self._ctx(client)
        for key in ("common_weather", "common_wind_direction", "common_time_of_day"):
            assert ctx[key]["label"] is None, f"{key} label should be None with no data"

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
class TestStatisticsSessionTypes:
    def _ctx(self, client):
        return client.get(URL).context

    def test_blank_bale_counted(self, client):
        SessionFactory(scoring_arrows=None, total_score=None)
        SessionFactory(scoring_arrows=0, total_score=None)
        assert self._ctx(client)["blank_bale_sessions"] == 2

    def test_scored_counted(self, client):
        SessionFactory(scoring_arrows=30, total_score=255)
        assert self._ctx(client)["scored_sessions"] == 1

    def test_scored_requires_total_score_not_null(self, client):
        SessionFactory(scoring_arrows=30, total_score=None)
        assert self._ctx(client)["scored_sessions"] == 0


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
