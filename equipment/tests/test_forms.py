import pytest

from equipment.forms import BowForm


@pytest.mark.django_db
class TestBowForm:
    def test_valid_minimal(self):
        form = BowForm({"name": "Test Bow", "type": "olympic_recurve"})
        assert form.is_valid()

    def test_name_required(self):
        form = BowForm({"type": "olympic_recurve"})
        assert not form.is_valid()
        assert "name" in form.errors

    def test_type_required(self):
        form = BowForm({"name": "Test Bow"})
        assert not form.is_valid()
        assert "type" in form.errors

    def test_draw_weight_optional(self):
        form = BowForm({"name": "Test Bow", "type": "olympic_recurve", "draw_weight_lbs": ""})
        assert form.is_valid()

    def test_notes_optional(self):
        form = BowForm({"name": "Test Bow", "type": "olympic_recurve", "notes": ""})
        assert form.is_valid()

    def test_valid_with_all_fields(self):
        form = BowForm({
            "name": "Blue Hoyt",
            "type": "olympic_recurve",
            "draw_weight_lbs": "28.5",
            "notes": "Competition bow",
        })
        assert form.is_valid()
        bow = form.save()
        assert bow.pk is not None
        assert float(bow.draw_weight_lbs) == 28.5
