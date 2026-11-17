from django.contrib.sitemaps import Sitemap
from django.db.models import Prefetch
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.portfolio.models import Competence, Parcours, Projet

from .donnees import donnees_site
from .models import PageStatique, SectionPublique

COMPETENCES_ACCUEIL = 9  # trois lignes de trois
PARCOURS_ACCUEIL = 3  # lignes par famille (formations, expériences, certifications)


def section_ou_404(cle):
    """Une section masquée répond par une page 404."""
    section = donnees_site()["sections"].get(cle)
    if section is None:
        raise Http404("Section masquée ou inexistante")
    return section


def section_visible(cle):
    return cle in donnees_site()["sections"]


def accueil(request):
    section = donnees_site()["toutes_sections"].get("accueil")
    contexte = {
        "section": section, "projets_vedette": [], "competences_cles": [], "parcours_groupes": [],
    }
    if section_visible("projets"):
        contexte["projets_vedette"] = (
            Projet.objects.publies()
            .filter(mis_en_avant=True)
            .select_related("categorie")
            .prefetch_related(
                Prefetch("technologies", queryset=Competence.objects.publiques())
            )[:5]
        )
    if section_visible("competences"):
        competences = Competence.objects.publiques().prefetch_related(
            Prefetch("projets", queryset=Projet.objects.publies())
        )
        cles = list(competences.filter(mise_en_avant=True)[:COMPETENCES_ACCUEIL])
        # Sans compétence clé cochée, l'accueil montre quand même les premières.
        contexte["competences_cles"] = cles or list(competences[:COMPETENCES_ACCUEIL])
    if section_visible("parcours"):
        contexte["parcours_groupes"] = Parcours.objects.par_famille(limite=PARCOURS_ACCUEIL)
    return render(request, "accueil.html", contexte)


def apropos(request):
    return render(request, "apropos.html", {"section": section_ou_404("apropos")})


def page(request, slug):
    objet = get_object_or_404(PageStatique, slug=slug, visible=True)
    return render(request, "page.html", {"page": objet})


def robots(request):
    plan = request.build_absolute_uri(reverse("sitemap"))
    return HttpResponse(f"User-agent: *\nAllow: /\n\nSitemap: {plan}\n", content_type="text/plain")


class PlanSections(Sitemap):
    def items(self):
        return list(SectionPublique.objects.filter(visible=True))


class PlanProjets(Sitemap):
    def items(self):
        if not section_visible("projets"):
            return []
        return list(Projet.objects.publies())


class PlanPages(Sitemap):
    def items(self):
        return list(PageStatique.objects.filter(visible=True))


PLANS = {"sections": PlanSections, "projets": PlanProjets, "pages": PlanPages}
