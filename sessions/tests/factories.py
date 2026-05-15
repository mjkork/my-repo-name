import datetime

import factory

from equipment.tests.factories import BowFactory
from sessions.models import Session


class SessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Session

    name = factory.Sequence(lambda n: f"Session {n}")
    date = factory.LazyFunction(datetime.date.today)
    bow = factory.SubFactory(BowFactory)
    location = Session.Location.INDOOR
    session_type = Session.SessionType.FREE_PRACTICE
