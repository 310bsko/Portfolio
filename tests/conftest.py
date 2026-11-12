import io

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


@pytest.fixture(autouse=True)
def environnement(db, settings, tmp_path):
    """Chaque test a sa base, un dossier de médias temporaire et un cache vide."""
    settings.MEDIA_ROOT = tmp_path
    cache.clear()


def fabriquer_image(format="PNG", taille=(40, 30), nom=None, exif=None):
    tampon = io.BytesIO()
    options = {"exif": exif} if exif else {}
    Image.new("RGB", taille, "#2563EB").save(tampon, format=format, **options)
    nom = nom or f"photo.{format.lower()}"
    return SimpleUploadedFile(nom, tampon.getvalue(), content_type=f"image/{format.lower()}")


@pytest.fixture
def image():
    return fabriquer_image()


@pytest.fixture
def proprietaire(django_user_model):
    return django_user_model.objects.create_superuser(
        "moi", "moi@example.com", "Un-Mot2Passe-Long!"
    )
