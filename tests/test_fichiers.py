"""Validation des téléversements : taille, type réel, EXIF, noms régénérés."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.core.fichiers import valider_image, valider_pdf
from apps.core.models import Profil
from apps.core.stockage import _identifiant
from apps.portfolio.models import Projet

from .conftest import fabriquer_image


@pytest.mark.parametrize("format", ["PNG", "JPEG", "WEBP"])
def test_formats_acceptes(format):
    valider_image(fabriquer_image(format))


def test_svg_refuse():
    svg = SimpleUploadedFile("logo.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>")
    with pytest.raises(ValidationError):
        valider_image(svg)


def test_faux_png_refuse():
    faux = SimpleUploadedFile("photo.png", b"ceci n'est pas une image", content_type="image/png")
    with pytest.raises(ValidationError):
        valider_image(faux)


def test_gif_refuse():
    with pytest.raises(ValidationError):
        valider_image(fabriquer_image("GIF"))


def test_image_trop_lourde_refusee(settings):
    settings.TAILLE_MAX_IMAGE = 100
    with pytest.raises(ValidationError):
        valider_image(fabriquer_image())


def test_exif_supprime_et_nom_regenere():
    exif = Image.Exif()
    exif[0x010F] = "AppareilSecret"
    exif[0x8825] = {1: "N", 2: (5.0, 20.0, 0.0)}  # coordonnées GPS
    envoi = fabriquer_image("JPEG", nom="IMG_vacances_2025.jpg", exif=exif.tobytes())
    assert b"AppareilSecret" in envoi.read()
    projet = Projet.objects.create(titre="Projet", image=envoi)
    assert "vacances" not in projet.image.name
    assert projet.image.name.startswith("projets/") and projet.image.name.endswith(".jpg")
    with projet.image.open("rb") as fichier:
        contenu = fichier.read()
    assert b"AppareilSecret" not in contenu
    with Image.open(projet.image.path) as image:
        assert not image.getexif()


def test_extension_corrigee_selon_le_type_reel():
    envoi = fabriquer_image("PNG", nom="photo.jpg")
    projet = Projet.objects.create(titre="Projet", image=envoi)
    assert projet.image.name.endswith(".png")


def test_pdf_valide_et_faux_pdf():
    valider_pdf(SimpleUploadedFile("cv.pdf", b"%PDF-1.7\n..."))
    with pytest.raises(ValidationError):
        valider_pdf(SimpleUploadedFile("cv.pdf", b"MZ executable"))


def test_pdf_trop_lourd(settings):
    settings.TAILLE_MAX_PDF = 10
    with pytest.raises(ValidationError):
        valider_pdf(SimpleUploadedFile("cv.pdf", b"%PDF-1.7 " + b"x" * 50))


def test_le_cv_se_telecharge_depuis_l_accueil(client):
    profil = Profil.charger()
    profil.cv = SimpleUploadedFile("mon cv.pdf", b"%PDF-1.7\n...")
    profil.save()
    assert profil.cv.name.startswith("cv/") and profil.cv.name.endswith(".pdf")
    assert profil.cv.url in client.get("/").content.decode()


def test_identifiants_cloudinary():
    assert _identifiant("projets/abc.jpg") == "projets/abc"
    assert _identifiant("cv/abc.pdf") == "cv/abc.pdf"


def test_cloudinary_recoit_le_contenu_d_une_image_nettoyee(monkeypatch):
    """Régression : un ContentFile sans nom était ignoré par le SDK (erreur 500 en ligne)."""
    import cloudinary.uploader
    import cloudinary.utils
    from django.core.files.base import ContentFile

    from apps.core.stockage import StockageCloudinary

    envoye = {}

    def faux_call_api(action, params, http_headers=None, return_error=False, unsigned=False,
                      file=None, timeout=None, **options):
        envoye["fichier"] = cloudinary.utils.handle_file_parameter(file, options.get("filename"))
        return {}

    monkeypatch.setattr(cloudinary.uploader, "call_api", faux_call_api)
    nom = StockageCloudinary().save("profil/abc.jpg", ContentFile(b"octets-image"))
    assert nom == "profil/abc.jpg"
    assert envoye["fichier"] == ("abc.jpg", b"octets-image")
