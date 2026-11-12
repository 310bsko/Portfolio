"""Données communes à toutes les pages publiques (en-tête, pied de page, SEO)."""

from django.conf import settings
from django.utils import timezone

from .models import PageStatique, ParametresSite, Profil, SectionPublique


def site(request):
    if request.path.startswith("/" + settings.ADMIN_URL):
        return {}
    profil = Profil.charger()
    parametres = ParametresSite.charger()
    menu = list(SectionPublique.objects.filter(visible=True))
    annee = timezone.localdate().year
    debut = parametres.copyright_debut
    return {
        "profil": profil,
        "parametres": parametres,
        "nom_site": parametres.nom_site or profil.nom_complet,
        "menu": menu,
        "sections": {section.cle: section for section in menu},
        "pages_pied": PageStatique.objects.filter(visible=True),
        "copyright_annees": f"{debut}–{annee}" if debut and debut < annee else str(annee),
    }
