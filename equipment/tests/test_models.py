import pytest

from accounts.tests.factories import UserFactory
from equipment.models import Bow, OlympicBowSetup
from equipment.tests.factories import BowFactory, OlympicBowSetupFactory


@pytest.mark.django_db
class TestBow:
    def test_str(self):
        bow = BowFactory(name="Blue Hoyt", type=Bow.BowType.OLYMPIC_RECURVE)
        assert str(bow) == "Blue Hoyt (Olympic Recurve)"

    def test_owner_fk(self):
        user = UserFactory()
        bow = BowFactory(owner=user)
        assert bow.owner == user

    def test_draw_weight_nullable(self):
        bow = BowFactory(draw_weight_lbs=None)
        bow.refresh_from_db()
        assert bow.draw_weight_lbs is None

    def test_draw_weight_stored(self):
        bow = BowFactory(draw_weight_lbs="28.5")
        bow.refresh_from_db()
        assert float(bow.draw_weight_lbs) == 28.5

    def test_notes_optional(self):
        bow = BowFactory(notes="")
        bow.refresh_from_db()
        assert bow.notes == ""

    def test_user_can_own_multiple_bows(self):
        user = UserFactory()
        BowFactory(owner=user)
        BowFactory(owner=user)
        assert Bow.objects.filter(owner=user).count() == 2

    def test_cascade_delete_with_owner(self):
        bow = BowFactory()
        owner = bow.owner
        owner.delete()
        assert not Bow.objects.filter(pk=bow.pk).exists()

    def test_ordering_by_name(self):
        user = UserFactory()
        BowFactory(owner=user, name="Zebra")
        BowFactory(owner=user, name="Alpha")
        names = list(Bow.objects.filter(owner=user).values_list("name", flat=True))
        assert names == ["Alpha", "Zebra"]


@pytest.mark.django_db
class TestOlympicBowSetup:
    def test_str(self):
        setup = OlympicBowSetupFactory(bow__name="Blue Hoyt")
        assert "Blue Hoyt" in str(setup)

    def test_one_to_one_with_bow(self):
        bow = BowFactory()
        setup = OlympicBowSetupFactory(bow=bow)
        assert setup.bow == bow
        assert bow.olympic_setup == setup

    def test_all_component_fields_optional(self):
        setup = OlympicBowSetupFactory()
        setup.refresh_from_db()
        component_fields = [
            "riser",
            "limbs",
            "arrow_rest",
            "sight",
            "main_stabilizer",
            "extender",
            "side_stabilizers",
            "v_bar",
            "clicker",
            "button",
        ]
        for field in component_fields:
            assert getattr(setup, field) == ""

    def test_component_fields_stored(self):
        setup = OlympicBowSetupFactory(riser="Hoyt Formula XI", sight="Shibuya Ultima")
        setup.refresh_from_db()
        assert setup.riser == "Hoyt Formula XI"
        assert setup.sight == "Shibuya Ultima"

    def test_cascade_delete_with_bow(self):
        setup = OlympicBowSetupFactory()
        bow = setup.bow
        bow.delete()
        assert not OlympicBowSetup.objects.filter(pk=setup.pk).exists()
