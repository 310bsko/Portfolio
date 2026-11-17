"""Données communes à toutes les pages publiques (en-tête, pied de page, SEO)."""

from django.conf import settings
from django.utils import timezone

from .donnees import donnees_site


def site(request):
    if request.path.startswith("/" + settings.ADMIN_URL):
        return {}
    donnees = donnees_site()
    profil = donnees["profil"]
    parametres = donnees["parametres"]
    annee = timezone.localdate().year
    debut = parametres.copyright_debut
    return {
        "profil": profil,
        "parametres": parametres,
        "nom_site": parametres.nom_site or profil.nom_complet,
        "menu": donnees["menu"],
        "sections": donnees["sections"],
        "pages_pied": donnees["pages_pied"],
        "copyright_annees": f"{debut}–{annee}" if debut and debut < annee else str(annee),
        "statistiques_vercel": settings.STATISTIQUES_VERCEL,
    }
