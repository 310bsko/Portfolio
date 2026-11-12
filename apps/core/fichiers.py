"""Téléversements : validation (taille, type réel), nettoyage EXIF, noms régénérés.

Règles du cahier des charges (3.3 et 7) :
- images JPEG, PNG ou WebP de 2 Mo au maximum, SVG refusé, métadonnées supprimées ;
- CV en PDF de 4 Mo au maximum, type réel vérifié ;
- le nom d'origine du fichier n'est jamais conservé.
"""

import io
import uuid
from pathlib import PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.utils.deconstruct import deconstructible
from PIL import Image, ImageChops, ImageOps

FORMATS_IMAGE = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def _mo(octets):
    return f"{octets / (1024 * 1024):.0f} Mo"


def _format_reel(fichier):
    """Retourne le format réel de l'image (lu par Pillow), ou None si ce n'est pas une image."""
    position = fichier.tell() if hasattr(fichier, "tell") else 0
    try:
        fichier.seek(0)
        with Image.open(fichier) as image:
            image.verify()
            return image.format
    except Exception:
        return None
    finally:
        fichier.seek(position)


def _deja_enregistre(fichier):
    """Fichier déjà stocké (validé à son envoi) : on ne le relit pas.

    Sans ce test, réenregistrer une fiche demandait la taille du fichier au stockage
    Cloudinary, qui ne la fournit pas (NotImplementedError, erreur 500).
    """
    return getattr(fichier, "_committed", False) is True


def valider_image(fichier):
    if _deja_enregistre(fichier):
        return
    if fichier.size > settings.TAILLE_MAX_IMAGE:
        raise ValidationError(
            f"L'image dépasse {_mo(settings.TAILLE_MAX_IMAGE)}. Réduisez-la avant de l'envoyer."
        )
    if _format_reel(fichier) not in FORMATS_IMAGE:
        raise ValidationError("Format refusé : envoyez une image JPEG, PNG ou WebP (pas de SVG).")


def valider_pdf(fichier):
    if _deja_enregistre(fichier):
        return
    if fichier.size > settings.TAILLE_MAX_PDF:
        raise ValidationError(f"Le PDF dépasse {_mo(settings.TAILLE_MAX_PDF)}.")
    position = fichier.tell() if hasattr(fichier, "tell") else 0
    fichier.seek(0)
    debut = fichier.read(5)
    fichier.seek(position)
    if debut != b"%PDF-":
        raise ValidationError("Ce fichier n'est pas un vrai PDF.")


def rogner_marges(image, seuil=24, respiration=0.04):
    """Retire les marges blanches ou transparentes autour d'un logo.

    Beaucoup de logos sont fournis dans un carré avec de grandes marges : une fois
    affichés dans une petite pastille, ils deviennent minuscules. On garde une légère
    marge (4 % de la plus grande dimension) pour que le logo ne touche pas le bord.
    """
    rgba = image.convert("RGBA")
    opaque = rgba.getchannel("A").point(lambda a: 255 if a > 8 else 0)
    blanc = Image.new("RGB", rgba.size, (255, 255, 255))
    colore = ImageChops.difference(rgba.convert("RGB"), blanc).convert("L")
    colore = colore.point(lambda v: 255 if v > seuil else 0)
    boite = ImageChops.multiply(opaque, colore).getbbox()
    if not boite:
        return image
    largeur, hauteur = image.size
    marge = round(max(boite[2] - boite[0], boite[3] - boite[1]) * respiration)
    boite = (
        max(0, boite[0] - marge), max(0, boite[1] - marge),
        min(largeur, boite[2] + marge), min(hauteur, boite[3] + marge),
    )
    return image.crop(boite)


def nettoyer_image(fichier, rogner=False):
    """Réenregistre l'image sans métadonnées (EXIF, GPS…), orientation appliquée.

    Avec `rogner=True` (logos, icônes), les marges vides autour de l'image sont retirées.
    """
    fichier.seek(0)
    with Image.open(fichier) as image:
        format_reel = image.format
        image = ImageOps.exif_transpose(image)
        if rogner:
            image = rogner_marges(image)
        if format_reel == "JPEG" and image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        elif image.mode == "P":
            image = image.convert("RGBA")
        # Copie des seuls pixels : aucune métadonnée de l'original n'est reprise.
        propre = Image.new(image.mode, image.size)
        propre.paste(image)
        sortie = io.BytesIO()
        options = {"JPEG": {"quality": 88, "optimize": True}, "WEBP": {"quality": 88}}
        propre.save(sortie, format=format_reel, **options.get(format_reel, {"optimize": True}))
    return sortie.getvalue(), FORMATS_IMAGE[format_reel]


@deconstructible
class Chemin:
    """Range le fichier dans un dossier, sous un nom aléatoire."""

    def __init__(self, dossier):
        self.dossier = dossier

    def __call__(self, instance, nom):
        extension = PurePosixPath(nom).suffix.lower()
        return f"{self.dossier}/{uuid.uuid4().hex}{extension}"


class ChampImage(models.ImageField):
    """Image validée, nettoyée de ses métadonnées avant d'être stockée.

    `rogner=True` retire les marges vides : à réserver aux logos et icônes (jamais aux photos).
    """

    default_validators = [valider_image]

    def __init__(self, *args, rogner=False, **kwargs):
        self.rogner = rogner
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        nom, chemin, args, kwargs = super().deconstruct()
        if self.rogner:
            kwargs["rogner"] = True
        return nom, chemin, args, kwargs

    def pre_save(self, instance, add):
        fichier = getattr(instance, self.attname)
        if fichier and not fichier._committed:
            contenu, extension = nettoyer_image(fichier.file, rogner=self.rogner)
            fichier.name = str(PurePosixPath(fichier.name).with_suffix(extension))
            fichier.file = ContentFile(contenu)
        return super().pre_save(instance, add)


class ChampPDF(models.FileField):
    """PDF dont le type réel et la taille sont vérifiés."""

    default_validators = [valider_pdf]
