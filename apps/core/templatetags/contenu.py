"""Filtres de gabarit : Markdown nettoyé, adresses d'images redimensionnées."""

import markdown as md
import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

BALISES = nh3.ALLOWED_TAGS - {"img"}


@register.filter
def markdown(texte):
    """Convertit le Markdown en HTML, puis le nettoie (aucun script, aucun style)."""
    if not texte:
        return ""
    html = md.markdown(texte, extensions=["extra", "sane_lists", "nl2br"])
    propre = nh3.clean(html, tags=BALISES, link_rel="noopener noreferrer nofollow")
    # Le code ne doit pas être déformé par la traduction automatique du navigateur.
    propre = propre.replace("<code>", '<code translate="no">').replace(
        "<pre>", '<pre translate="no">'
    )
    return mark_safe(propre)  # noqa: S308 — HTML nettoyé par nh3 juste au-dessus


@register.filter
def premier_paragraphe(texte):
    """Premier paragraphe d'un texte Markdown (première ligne non vide), pour un aperçu."""
    for ligne in (texte or "").splitlines():
        if ligne.strip():
            return markdown(ligne.strip())
    return ""


@register.filter
def image(fichier, largeur=None):
    """Adresse de l'image, redimensionnée et convertie par Cloudinary quand il est actif."""
    if not fichier:
        return ""
    stockage = fichier.storage
    if hasattr(stockage, "url_image"):
        return stockage.url_image(fichier.name, largeur)
    return fichier.url
