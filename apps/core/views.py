from django.contrib.sitemaps import Sitemap
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.portfolio.models import Competence, Projet

from .models import PageStatique, SectionPublique


def section_ou_404(cle):
    """Une section masquée répond par une page 404."""
    return get_object_or_404(SectionPublique, cle=cle, visible=True)


def section_visible(cle):
    return SectionPublique.objects.filter(cle=cle, visible=True).exists()


def accueil(request):
    section = SectionPublique.objects.filter(cle="accueil").first()
    contexte = {"section": section, "projets_vedette": [], "competences_cles": []}
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
        contexte["competences_cles"] = Competence.objects.publiques().filter(mise_en_avant=True)
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
