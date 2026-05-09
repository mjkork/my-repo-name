import factory

from accounts.tests.factories import UserFactory
from equipment.models import Bow, OlympicBowSetup


class BowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Bow

    owner = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Bow {n}")
    type = Bow.BowType.OLYMPIC_RECURVE
    draw_weight_lbs = None
    notes = ""


class OlympicBowSetupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OlympicBowSetup

    bow = factory.SubFactory(BowFactory)
    riser = ""
    limbs = ""
    arrow_rest = ""
    sight = ""
    main_stabilizer = ""
    extender = ""
    side_stabilizers = ""
    v_bar = ""
    clicker = ""
    button = ""
