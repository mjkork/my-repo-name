import pytest

from equipment.forms import BowForm, OlympicBowSetupForm
from equipment.tests.factories import BowFactory


@pytest.mark.django_db
class TestBowForm:
    def test_valid_minimal(self):
        form = BowForm({"bow-name": "Test Bow", "bow-type": "olympic_recurve"}, prefix="bow")
        assert form.is_valid()

    def test_name_required(self):
        form = BowForm({"bow-type": "olympic_recurve"}, prefix="bow")
        assert not form.is_valid()
        assert "name" in form.errors

    def test_type_required(self):
        form = BowForm({"bow-name": "Test Bow"}, prefix="bow")
        assert not form.is_valid()
        assert "type" in form.errors

    def test_draw_weight_optional(self):
        form = BowForm(
            {"bow-name": "Test Bow", "bow-type": "olympic_recurve", "bow-draw_weight_lbs": ""},
            prefix="bow",
        )
        assert form.is_valid()

    def test_notes_optional(self):
        form = BowForm(
            {"bow-name": "Test Bow", "bow-type": "olympic_recurve", "bow-notes": ""},
            prefix="bow",
        )
        assert form.is_valid()

    def test_valid_with_all_fields(self):
        form = BowForm({
            "bow-name": "Blue Hoyt",
            "bow-type": "olympic_recurve",
            "bow-draw_weight_lbs": "28.5",
            "bow-notes": "Competition bow",
        }, prefix="bow")
        assert form.is_valid()
        bow = form.save()
        assert bow.pk is not None
        assert float(bow.draw_weight_lbs) == 28.5


@pytest.mark.django_db
class TestOlympicBowSetupForm:
    def test_all_fields_optional(self):
        form = OlympicBowSetupForm({}, prefix="setup")
        assert form.is_valid()

    def test_component_fields_saved(self):
        bow = BowFactory()
        form = OlympicBowSetupForm({
            "setup-riser": "Hoyt Formula XI",
            "setup-limbs": "Uukha EX1",
            "setup-sight": "Shibuya Ultima",
        }, prefix="setup")
        assert form.is_valid()
        setup = form.save(commit=False)
        setup.bow = bow
        setup.save()
        assert setup.riser == "Hoyt Formula XI"
        assert setup.limbs == "Uukha EX1"
        assert setup.sight == "Shibuya Ultima"

    def test_empty_strings_for_unset_fields(self):
        bow = BowFactory()
        form = OlympicBowSetupForm({}, prefix="setup")
        assert form.is_valid()
        setup = form.save(commit=False)
        setup.bow = bow
        setup.save()
        assert setup.riser == ""
        assert setup.clicker == ""
