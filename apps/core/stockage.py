"""Backend de stockage Django pour Cloudinary, écrit avec le SDK officiel (décision D7).

Activé seulement si la variable CLOUDINARY_URL est définie ; en local, les fichiers
restent dans le dossier `media/`.

Les images sont envoyées comme ressources « image » (redimensionnées et converties en WebP
à la livraison) ; les PDF comme ressources « raw ». Pour que le CV se télécharge, l'option
« Allow delivery of PDF and ZIP files » doit être cochée dans Settings > Security.
"""

import urllib.request
from pathlib import PurePosixPath

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

EXTENSIONS_IMAGE = {".jpg", ".jpeg", ".png", ".webp"}


def _est_image(nom):
    return PurePosixPath(nom).suffix.lower() in EXTENSIONS_IMAGE


def _identifiant(nom):
    """Identifiant public Cloudinary : sans extension pour une image, complet pour un PDF."""
    nom = nom.replace("\\", "/")
    return str(PurePosixPath(nom).with_suffix("")) if _est_image(nom) else nom


@deconstructible
class StockageCloudinary(Storage):
    def _save(self, name, content):
        name = name.replace("\\", "/")
        content.seek(0)
        cloudinary.uploader.upload(
            content,
            public_id=_identifiant(name),
            resource_type="image" if _est_image(name) else "raw",
            overwrite=True,
            invalidate=True,
        )
        return name

    def _open(self, name, mode="rb"):
        with urllib.request.urlopen(self.url(name), timeout=20) as reponse:  # noqa: S310
            return ContentFile(reponse.read(), name=name)

    def url(self, name):
        if _est_image(name):
            return self.url_image(name)
        return cloudinary.utils.cloudinary_url(name, resource_type="raw", secure=True)[0]

    def url_image(self, name, largeur=None):
        """Adresse d'une image convertie (WebP/AVIF selon le navigateur) et redimensionnée."""
        options = {"fetch_format": "auto", "quality": "auto", "secure": True}
        if largeur:
            options.update(width=int(largeur), crop="limit")
        return cloudinary.utils.cloudinary_url(_identifiant(name), **options)[0]

    def delete(self, name):
        cloudinary.uploader.destroy(
            _identifiant(name),
            resource_type="image" if _est_image(name) else "raw",
            invalidate=True,
        )

    def exists(self, name):
        # Les noms sont aléatoires (voir fichiers.Chemin) : aucune collision à gérer.
        return False

    def get_available_name(self, name, max_length=None):
        return name.replace("\\", "/")
