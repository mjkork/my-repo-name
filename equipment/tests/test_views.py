import pytest
from django.urls import reverse

from equipment.models import Bow, OlympicBowSetup
from equipment.tests.factories import BowFactory, OlympicBowSetupFactory


def _modify_url(pk):
    return reverse("equipment:modifybow", kwargs={"pk": pk})


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


@pytest.mark.django_db
class TestModifyBowView:
    def test_url_resolves(self):
        url = reverse("equipment:modifybow", kwargs={"pk": 42})
        assert url == "/mybows/42/modify/"

    def test_get_returns_200(self, client):
        bow = BowFactory()
        OlympicBowSetupFactory(bow=bow)
        response = client.get(_modify_url(bow.pk))
        assert response.status_code == 200

    def test_get_includes_bow_name(self, client):
        bow = BowFactory(name="Blue Hoyt")
        OlympicBowSetupFactory(bow=bow)
        response = client.get(_modify_url(bow.pk))
        assert b"Blue Hoyt" in response.content

    def test_get_sets_modify_pk_in_context(self, client):
        bow = BowFactory()
        OlympicBowSetupFactory(bow=bow)
        response = client.get(_modify_url(bow.pk))
        assert response.context["modify_pk"] == bow.pk

    def test_get_404_for_nonexistent_bow(self, client):
        response = client.get(_modify_url(9999))
        assert response.status_code == 404

    def test_valid_post_updates_bow_name(self, client):
        bow = BowFactory(name="Old Name")
        OlympicBowSetupFactory(bow=bow)
        client.post(_modify_url(bow.pk), {
            "modify-name": "New Name",
            "modify-type": "olympic_recurve",
        })
        bow.refresh_from_db()
        assert bow.name == "New Name"

    def test_valid_post_redirects_to_mybows(self, client):
        bow = BowFactory()
        OlympicBowSetupFactory(bow=bow)
        response = client.post(_modify_url(bow.pk), {
            "modify-name": bow.name,
            "modify-type": bow.type,
        })
        assert response.status_code == 302
        assert response["Location"] == reverse("equipment:mybows")

    def test_valid_post_updates_component_fields(self, client):
        bow = BowFactory()
        OlympicBowSetupFactory(bow=bow, riser="Old Riser", sight="")
        client.post(_modify_url(bow.pk), {
            "modify-name": bow.name,
            "modify-type": bow.type,
            "modsetup-riser": "New Riser",
            "modsetup-sight": "Shibuya Ultima",
        })
        bow.olympic_setup.refresh_from_db()
        assert bow.olympic_setup.riser == "New Riser"
        assert bow.olympic_setup.sight == "Shibuya Ultima"

    def test_invalid_post_does_not_update(self, client):
        bow = BowFactory(name="Blue Hoyt")
        OlympicBowSetupFactory(bow=bow)
        client.post(_modify_url(bow.pk), {
            "modify-name": "",  # required — should fail validation
            "modify-type": "olympic_recurve",
        })
        bow.refresh_from_db()
        assert bow.name == "Blue Hoyt"

    def test_invalid_post_rerenders_with_errors(self, client):
        bow = BowFactory()
        OlympicBowSetupFactory(bow=bow)
        response = client.post(_modify_url(bow.pk), {
            "modify-name": "",
            "modify-type": "olympic_recurve",
        })
        assert response.status_code == 200
        assert response.context["modify_bow_form"].errors

    def test_invalid_post_sets_modify_pk_in_context(self, client):
        bow = BowFactory()
        OlympicBowSetupFactory(bow=bow)
        response = client.post(_modify_url(bow.pk), {
            "modify-name": "",
            "modify-type": "olympic_recurve",
        })
        assert response.context["modify_pk"] == bow.pk
