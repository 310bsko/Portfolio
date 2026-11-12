"""Règles de gestion : visibilité, publication, ordre, sections, champs obligatoires."""

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.core.models import PageStatique, ParametresSite, Profil, SectionPublique
from apps.core.templatetags.contenu import markdown
from apps.portfolio.models import Categorie, Collaboration, Competence, Parcours, Projet


def section(cle):
    return SectionPublique.objects.get(cle=cle)


# --- Visibilité et statut de publication


def test_un_brouillon_n_est_pas_public(client):
    Projet.objects.create(titre="Secret")
    assert "Secret" not in client.get(reverse("projets")).content.decode()
    assert client.get("/projets/secret/").status_code == 404


def test_un_projet_publie_est_visible_sans_redeployer(client):
    projet = Projet.objects.create(titre="Pipeline météo", statut="publie", mis_en_avant=True)
    assert "Pipeline météo" in client.get(reverse("projets")).content.decode()
    assert "Pipeline météo" in client.get(reverse("accueil")).content.decode()
    assert client.get(projet.get_absolute_url()).status_code == 200


def test_une_competence_masquee_n_apparait_pas(client):
    Competence.objects.create(nom="Python")
    Competence.objects.create(nom="Cobol", visible=False)
    page = client.get(reverse("competences")).content.decode()
    assert "Python" in page
    assert "Cobol" not in page


def test_parcours_et_collaborations_masques(client):
    Parcours.objects.create(titre="Master Data", type="formation")
    Parcours.objects.create(titre="Ancien job", type="experience", visible=False)
    Collaboration.objects.create(nom="Awa")
    Collaboration.objects.create(nom="Caché", visible=False)
    parcours = client.get(reverse("parcours")).content.decode()
    collaborations = client.get(reverse("collaborations")).content.decode()
    assert "Master Data" in parcours and "Ancien job" not in parcours
    assert "Awa" in collaborations and "Caché" not in collaborations


def test_filtre_par_categorie(client):
    data = Categorie.objects.create(nom="Data", domaine="projet")
    Projet.objects.create(titre="Projet A", statut="publie", categorie=data)
    Projet.objects.create(titre="Projet B", statut="publie")
    page = client.get(reverse("projets"), {"categorie": "data"}).content.decode()
    assert "Projet A" in page
    assert "Projet B" not in page


# --- Ordre


def test_un_nouvel_element_est_place_en_dernier(client):
    premier = Projet.objects.create(titre="Premier", statut="publie")
    second = Projet.objects.create(titre="Second", statut="publie")
    assert second.ordre > premier.ordre
    second.ordre = 0  # 0 = « en dernier » : recalculé à l'enregistrement
    premier.ordre = 10
    premier.save()
    page = client.get(reverse("projets")).content.decode()
    assert page.index("Second") < page.index("Premier")


def test_parcours_antechronologique_puis_ordre_manuel():
    Parcours.objects.create(titre="Sans date", type="certification")
    Parcours.objects.create(titre="Ancien", type="stage", date_debut="2023-01-01")
    Parcours.objects.create(titre="Récent", type="formation", date_debut="2025-09-01")
    titres = [ligne.titre for ligne in Parcours.objects.chronologie()]
    assert titres == ["Récent", "Ancien", "Sans date"]


# --- Sections


@pytest.mark.parametrize("cle", ["apropos", "projets", "competences", "parcours",
                                 "collaborations", "contact"])
def test_une_section_masquee_disparait_et_repond_404(client, cle):
    objet = section(cle)
    adresse = objet.get_absolute_url()
    assert client.get(adresse).status_code == 200
    objet.visible = False
    objet.save()
    assert client.get(adresse).status_code == 404
    accueil = client.get(reverse("accueil")).content.decode()
    assert f'href="{adresse}"' not in accueil
    assert adresse not in client.get(reverse("sitemap")).content.decode()


def test_projet_inaccessible_si_la_section_projets_est_masquee(client):
    projet = Projet.objects.create(titre="Visible", statut="publie", mis_en_avant=True)
    SectionPublique.objects.filter(cle="projets").update(visible=False)
    assert client.get(projet.get_absolute_url()).status_code == 404
    assert "Visible" not in client.get(reverse("accueil")).content.decode()


def test_l_accueil_ne_peut_pas_etre_masque():
    accueil = section("accueil")
    accueil.visible = False
    with pytest.raises(ValidationError):
        accueil.full_clean()
    accueil.save()
    accueil.refresh_from_db()
    assert accueil.visible is True


def test_les_titres_de_section_viennent_de_l_administration(client):
    SectionPublique.objects.filter(cle="projets").update(titre="Mes réalisations")
    page = client.get(reverse("projets")).content.decode()
    assert "Mes réalisations</span></span></h1>" in page


# --- Champs obligatoires (D6) : seul le nom ou le titre est requis


def test_un_projet_avec_seulement_un_titre_peut_etre_publie(client):
    projet = Projet(titre="Juste un titre", statut="publie")
    projet.full_clean()
    projet.save()
    assert projet.slug == "juste-un-titre"
    for adresse in [reverse("projets"), projet.get_absolute_url()]:
        page = client.get(adresse).content.decode()
        assert "Juste un titre" in page
        assert "None" not in page
        assert "Technologies" not in page and "Contexte" not in page and "Galerie" not in page


def test_un_projet_sans_titre_est_refuse():
    with pytest.raises(ValidationError):
        Projet(titre="").full_clean()


def test_competence_et_collaboration_avec_seulement_un_nom(client):
    Competence(nom="Spark").full_clean()
    Collaboration(nom="Awa").full_clean()
    Competence.objects.create(nom="Spark")
    Collaboration.objects.create(nom="Awa")
    assert "Spark" in client.get(reverse("competences")).content.decode()
    page = client.get(reverse("collaborations")).content.decode()
    assert "Awa" in page and "None" not in page


def test_parcours_exige_un_titre_et_un_type():
    with pytest.raises(ValidationError):
        Parcours(titre="Sans type").full_clean()
    Parcours(titre="Master", type="formation").full_clean()


def test_les_slugs_sont_uniques():
    premier = Projet.objects.create(titre="Même titre")
    second = Projet.objects.create(titre="Même titre")
    assert premier.slug != second.slug


def test_competence_sans_categorie_dans_autres(client):
    langages = Categorie.objects.create(nom="Langages", domaine="competence")
    Competence.objects.create(nom="Python", categorie=langages)
    Competence.objects.create(nom="Git")
    page = client.get(reverse("competences")).content.decode()
    assert "<h2>Autres</h2>" in page


# --- Suppression


def test_supprimer_une_categorie_ou_une_competence_ne_supprime_pas_le_projet():
    data = Categorie.objects.create(nom="Data", domaine="projet")
    python = Competence.objects.create(nom="Python")
    projet = Projet.objects.create(titre="Projet", categorie=data)
    projet.technologies.add(python)
    data.delete()
    python.delete()
    projet.refresh_from_db()
    assert projet.categorie is None
    assert projet.technologies.count() == 0


# --- Lignes uniques et moyens de contact


def test_profil_et_parametres_n_ont_qu_une_ligne():
    Profil(prenom="Autre", nom="Personne").save()
    ParametresSite().save()
    assert Profil.objects.count() == 1
    assert ParametresSite.objects.count() == 1


def test_au_moins_un_moyen_de_contact():
    parametres = ParametresSite.charger()
    parametres.formulaire_actif = False
    with pytest.raises(ValidationError):
        parametres.full_clean()
    Profil.objects.update(email_public="moi@example.com")
    parametres.full_clean()


# --- Contenu, SEO, cache


def test_le_markdown_est_nettoye():
    html = markdown("**gras** <script>alert(1)</script> [lien](javascript:alert(1)) `code`")
    assert "<strong>gras</strong>" in html
    assert "<script" not in html and "javascript:" not in html
    assert '<code translate="no">' in html


def test_pages_legales_editables(client):
    page = PageStatique.objects.get(slug="mentions-legales")
    assert client.get(page.get_absolute_url()).status_code == 200
    page.visible = False
    page.save()
    assert client.get(page.get_absolute_url()).status_code == 404


def test_seo_de_base(client):
    Profil.objects.update(prenom="Awa", nom="Koné")
    page = client.get(reverse("projets")).content.decode()
    assert "<title>Projets · Awa Koné</title>" in page
    assert 'lang="fr"' in page and 'rel="canonical"' in page
    assert client.get("/robots.txt").status_code == 200
    assert "<loc>" in client.get("/sitemap.xml").content.decode()


def test_cache_des_pages_publiques_60_secondes_sauf_contact(client):
    assert "s-maxage=60" in client.get(reverse("accueil"))["Cache-Control"]
    assert "s-maxage=60" in client.get(reverse("projets"))["Cache-Control"]
    controle = client.get(reverse("contact"))["Cache-Control"]
    assert "no-store" in controle and "s-maxage" not in controle


def test_page_404_personnalisee(client):
    reponse = client.get("/cette-page-n-existe-pas/")
    assert reponse.status_code == 404
    assert "Page introuvable" in reponse.content.decode()
