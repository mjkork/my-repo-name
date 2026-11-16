from analytics.services import build_bar_rows


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
