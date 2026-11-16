from analytics.services import build_bar_rows, build_scale_marker


class TestBuildBarRows:
    def test_percent_and_width_relative_to_largest(self):
        rows = build_bar_rows([("A", 10), ("B", 5)])
        assert rows[0] == {"label": "A", "count": 10, "percent": 67, "width": 100}
        assert rows[1] == {"label": "B", "count": 5, "percent": 33, "width": 50}

    def test_largest_count_always_gets_width_100(self):
        rows = build_bar_rows([("A", 3), ("B", 1), ("C", 2)])
        assert rows[0]["width"] == 100

    def test_small_nonzero_count_gets_at_least_width_2(self):
        rows = build_bar_rows([("A", 100), ("B", 1)])
        assert rows[1]["width"] == 2

    def test_zero_count_gets_width_0(self):
        rows = build_bar_rows([("A", 5), ("B", 0)])
        assert rows[1]["width"] == 0
        assert rows[1]["percent"] == 0

    def test_all_zero_counts_no_division_by_zero(self):
        rows = build_bar_rows([("A", 0), ("B", 0)])
        assert rows == [
            {"label": "A", "count": 0, "percent": 0, "width": 0},
            {"label": "B", "count": 0, "percent": 0, "width": 0},
        ]

    def test_empty_input_returns_empty_list(self):
        assert build_bar_rows([]) == []


_LABELS = ["Very low", "Low", "Medium", "High", "Very high"]


class TestBuildScaleMarker:
    def test_average_1_0_gives_position_0_and_lowest_label(self):
        marker = build_scale_marker(1.0, _LABELS)
        assert marker["position"] == 0
        assert marker["nearest_label"] == "Very low"
        assert marker["average"] == "1.0"

    def test_average_5_0_gives_position_100_and_highest_label(self):
        marker = build_scale_marker(5.0, _LABELS)
        assert marker["position"] == 100
        assert marker["nearest_label"] == "Very high"

    def test_average_1_7_gives_position_17_5_and_rounds_to_label_2(self):
        marker = build_scale_marker(1.7, _LABELS)
        assert marker["position"] == 17.5
        assert marker["nearest_label"] == "Low"
        assert marker["average"] == "1.7"

    def test_average_2_5_rounds_half_up_to_label_3(self):
        """2.5 must round up to label 3 ("Medium"); Python's banker's
        rounding would give label 2 ("Low") instead."""
        marker = build_scale_marker(2.5, _LABELS)
        assert marker["nearest_label"] == "Medium"

    def test_low_and_high_labels_are_the_scale_ends(self):
        marker = build_scale_marker(3.0, _LABELS)
        assert marker["low_label"] == "Very low"
        assert marker["high_label"] == "Very high"
