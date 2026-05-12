import pytest
from django.urls import reverse

from equipment.models import Bow, OlympicBowSetup
from equipment.tests.factories import BowFactory, OlympicBowSetupFactory


@pytest.mark.django_db
class TestMyBowsView:
    def test_get_returns_200(self, client):
        response = client.get(reverse("equipment:mybows"))
        assert response.status_code == 200

    def test_empty_state_message(self, client):
        response = client.get(reverse("equipment:mybows"))
        assert b"No bows added" in response.content

    def test_bow_name_appears_in_list(self, client):
        BowFactory(name="Blue Hoyt")
        response = client.get(reverse("equipment:mybows"))
        assert b"Blue Hoyt" in response.content

    def test_no_empty_state_when_bows_exist(self, client):
        BowFactory()
        response = client.get(reverse("equipment:mybows"))
        assert b"No bows added" not in response.content

    def test_valid_post_creates_bow_and_setup(self, client):
        response = client.post(reverse("equipment:mybows"), {
            "bow-name": "Hoyt Prodigy",
            "bow-type": "olympic_recurve",
            "bow-draw_weight_lbs": "",
            "bow-notes": "",
        })
        assert response.status_code == 302
        bow = Bow.objects.get(name="Hoyt Prodigy")
        assert OlympicBowSetup.objects.filter(bow=bow).exists()

    def test_invalid_post_rerenders_with_errors(self, client):
        response = client.post(reverse("equipment:mybows"), {
            "bow-name": "",
            "bow-type": "olympic_recurve",
        })
        assert response.status_code == 200
        assert response.context["bow_form"].errors

    def test_new_bow_appears_after_add(self, client):
        client.post(reverse("equipment:mybows"), {
            "bow-name": "Samick Sage",
            "bow-type": "olympic_recurve",
            "bow-draw_weight_lbs": "26",
            "bow-notes": "",
        })
        response = client.get(reverse("equipment:mybows"))
        assert b"Samick Sage" in response.content

    def test_component_fields_saved(self, client):
        client.post(reverse("equipment:mybows"), {
            "bow-name": "Test Bow",
            "bow-type": "olympic_recurve",
            "setup-riser": "Hoyt Formula XI",
            "setup-sight": "Shibuya Ultima",
        })
        bow = Bow.objects.get(name="Test Bow")
        assert bow.olympic_setup.riser == "Hoyt Formula XI"
        assert bow.olympic_setup.sight == "Shibuya Ultima"
