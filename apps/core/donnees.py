"""Données lues sur toutes les pages : profil, paramètres, sections et pages légales.

Elles changent rarement. Chaque instance du serveur les garde donc en mémoire pendant
DUREE_CACHE_DONNEES secondes (60 en ligne, la même durée que le cache du CDN) au lieu de
les relire en base à chaque visite. Une modification faite dans l'administration vide
aussitôt cette mémoire sur l'instance qui l'a enregistrée ; les autres instances se mettent
à jour au plus tard 60 secondes après.
"""

import time

from django.conf import settings

_memoire = {"valeur": None, "expire": 0.0}


def donnees_site():
    maintenant = time.monotonic()
    if _memoire["valeur"] is None or maintenant >= _memoire["expire"]:
        from .models import PageStatique, ParametresSite, Profil, SectionPublique

        sections = list(SectionPublique.objects.all())
        visibles = [section for section in sections if section.visible]
        _memoire["valeur"] = {
            "profil": Profil.charger(),
            "parametres": ParametresSite.charger(),
            "toutes_sections": {section.cle: section for section in sections},
            "menu": visibles,
            "sections": {section.cle: section for section in visibles},
            "pages_pied": list(PageStatique.objects.filter(visible=True)),
        }
        _memoire["expire"] = maintenant + settings.DUREE_CACHE_DONNEES
    return _memoire["valeur"]


def vider_donnees_site(**kwargs):
    _memoire["valeur"] = None
