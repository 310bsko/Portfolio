"""Formulaire de contact (valide, invalide, spam) et accès à l'administration."""

import json
from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.contact.models import Message
from apps.core.models import ParametresSite, Profil
from apps.portfolio.models import Projet

VALIDE = {
    "nom": "Awa Koné",
    "email": "awa@example.com",
    "sujet": "Offre de stage",
    "contenu": "Bonjour, nous avons une offre de stage pour vous.",
    "site_web": "",
}
ADMIN = "/" + settings.ADMIN_URL


def test_message_valide_enregistre_et_notifie(client):
    ParametresSite.objects.update(email_notification="moi@example.com")
    ParametresSite.charger()
    reponse = client.post(reverse("contact"), VALIDE)
    assert reponse.status_code == 302
    message = Message.objects.get()
    assert message.nom == "Awa Koné" and message.lu is False
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["moi@example.com"]
    assert mail.outbox[0].reply_to == ["awa@example.com"]
    assert "bien été envoyé" in client.get(reponse.url).content.decode()


def test_message_invalide_refuse(client):
    reponse = client.post(reverse("contact"), {**VALIDE, "email": "pas-un-email", "contenu": "x"})
    assert reponse.status_code == 200
    assert Message.objects.count() == 0
    assert "champ__erreur" in reponse.content.decode()


def test_champ_piege_rempli_message_ignore(client):
    reponse = client.post(reverse("contact"), {**VALIDE, "site_web": "http://spam.example"})
    assert reponse.status_code == 302  # le robot croit avoir réussi
    assert Message.objects.count() == 0
    assert len(mail.outbox) == 0


def test_limitation_de_debit(client, settings):
    settings.CONTACT_DEBIT = "2/h"
    for _ in range(2):
        assert client.post(reverse("contact"), VALIDE).status_code == 302
    reponse = client.post(reverse("contact"), VALIDE)
    assert reponse.status_code == 429
    assert Message.objects.count() == 2


def test_post_sans_jeton_csrf_refuse():
    from django.test import Client

    assert Client(enforce_csrf_checks=True).post(reverse("contact"), VALIDE).status_code == 403


def test_formulaire_desactive(client):
    Profil.objects.update(email_public="moi@example.com")
    ParametresSite.objects.update(formulaire_actif=False)
    page = client.get(reverse("contact")).content.decode()
    assert "<form" not in page
    assert "moi@example.com" in page
    client.post(reverse("contact"), VALIDE)
    assert Message.objects.count() == 0


def test_purge_des_messages_de_plus_de_12_mois():
    ancien = Message.objects.create(nom="A", email="a@example.com", contenu="Vieux message")
    Message.objects.filter(pk=ancien.pk).update(date=timezone.now() - timedelta(days=400))
    Message.objects.create(nom="B", email="b@example.com", contenu="Message récent")
    call_command("purger_messages")
    assert list(Message.objects.values_list("nom", flat=True)) == ["B"]


# --- Administration réservée au propriétaire


def test_admin_inaccessible_sans_connexion(client):
    reponse = client.get(ADMIN)
    assert reponse.status_code == 302 and "login" in reponse.url
    assert client.get(ADMIN + "exporter/").status_code == 302
    assert client.get("/admin/").status_code == 404  # adresse standard inexistante


def test_admin_refuse_a_un_compte_non_proprietaire(client, django_user_model):
    django_user_model.objects.create_user("visiteur", password="Un-Mot2Passe-Long!")
    client.login(username="visiteur", password="Un-Mot2Passe-Long!")
    assert client.get(ADMIN).status_code == 302
    assert client.get(ADMIN + "exporter/").status_code == 302


def test_aucune_inscription_publique(client):
    for adresse in ["/inscription/", "/signup/", "/register/", "/accounts/signup/"]:
        assert client.get(adresse).status_code == 404


def test_le_proprietaire_accede_a_tout(client, proprietaire):
    client.force_login(proprietaire)
    for adresse in ["", "core/profil/", "core/parametressite/", "core/sectionpublique/",
                    "core/pagestatique/", "portfolio/projet/", "portfolio/projet/add/",
                    "portfolio/competence/", "portfolio/categorie/", "portfolio/parcours/",
                    "portfolio/collaboration/", "contact/message/"]:
        assert client.get(ADMIN + adresse, follow=True).status_code == 200, adresse


def test_ajout_d_un_projet_depuis_l_admin_avec_seulement_un_titre(client, proprietaire):
    client.force_login(proprietaire)
    donnees = {
        "titre": "Créé dans l'admin", "statut": "publie", "ordre": "0", "slug": "",
        "images-TOTAL_FORMS": "0", "images-INITIAL_FORMS": "0",
    }
    reponse = client.post(ADMIN + "portfolio/projet/add/", donnees, follow=True)
    assert reponse.status_code == 200
    projet = Projet.objects.get()
    assert projet.slug == "cree-dans-ladmin"
    # Avertissement non bloquant : publié sans résumé ni image.
    assert "Projet publié sans résumé ni image" in reponse.content.decode()
    assert "Créé dans l&#x27;admin" in client.get(reverse("projets")).content.decode()


def test_dupliquer_un_projet(client, proprietaire):
    client.force_login(proprietaire)
    original = Projet.objects.create(titre="Original", statut="publie")
    client.post(
        ADMIN + "portfolio/projet/",
        {"action": "dupliquer", "_selected_action": [original.pk]},
    )
    copie = Projet.objects.exclude(pk=original.pk).get()
    assert copie.titre == "Original (copie)" and copie.statut == "brouillon"
    assert copie.slug != original.slug


def test_export_complet_sans_les_messages(client, proprietaire):
    Projet.objects.create(titre="À sauvegarder")
    Message.objects.create(nom="A", email="a@example.com", contenu="Données personnelles")
    client.force_login(proprietaire)
    reponse = client.get(ADMIN + "exporter/")
    assert "attachment" in reponse["Content-Disposition"]
    modeles = {ligne["model"] for ligne in json.loads(reponse.content)}
    assert {"core.profil", "core.sectionpublique", "portfolio.projet"} <= modeles
    assert "contact.message" not in modeles
