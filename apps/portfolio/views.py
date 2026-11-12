from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from apps.core.views import section_ou_404

from .models import Categorie, Collaboration, Competence, Parcours, Projet

PROJETS_PUBLIES = Prefetch("projets", queryset=Projet.objects.publies())
TECHNOLOGIES = Prefetch("technologies", queryset=Competence.objects.publiques())


def projets(request):
    section = section_ou_404("projets")
    liste = Projet.objects.publies().select_related("categorie").prefetch_related(TECHNOLOGIES)
    categories = Categorie.objects.filter(
        domaine=Categorie.Domaine.PROJET, visible=True, projets__statut=Projet.Statut.PUBLIE
    ).distinct()
    active = categories.filter(slug=request.GET.get("categorie", "")).first()
    if active:
        liste = liste.filter(categorie=active)
    return render(
        request,
        "portfolio/projets.html",
        {"section": section, "projets": liste, "categories": categories, "active": active},
    )


def projet(request, slug):
    section_ou_404("projets")
    objet = get_object_or_404(
        Projet.objects.publies()
        .select_related("categorie")
        .prefetch_related(TECHNOLOGIES, "images"),
        slug=slug,
    )
    blocs = [
        (titre, texte)
        for titre, texte in [
            ("Contexte", objet.contexte),
            ("Problématique", objet.problematique),
            ("Solution", objet.solution),
            ("Mon rôle", objet.role),
            ("Résultats", objet.resultats),
        ]
        if texte.strip()
    ]
    return render(
        request,
        "portfolio/projet.html",
        {
            "projet": objet,
            "blocs": blocs,
            "collaborations": objet.collaborations.filter(visible=True),
        },
    )


def competences(request):
    section = section_ou_404("competences")
    base = Competence.objects.filter(visible=True).prefetch_related(PROJETS_PUBLIES)
    groupes = [
        (categorie.nom, list(categorie.liste))
        for categorie in Categorie.objects.filter(
            domaine=Categorie.Domaine.COMPETENCE, visible=True
        ).prefetch_related(Prefetch("competences", queryset=base, to_attr="liste"))
    ]
    groupes = [groupe for groupe in groupes if groupe[1]]
    autres = list(base.filter(categorie__isnull=True))
    if autres:
        groupes.append(("Autres" if groupes else "", autres))
    return render(request, "portfolio/competences.html", {"section": section, "groupes": groupes})


def parcours(request):
    section = section_ou_404("parcours")
    lignes = list(Parcours.objects.filter(visible=True).chronologie())
    T = Parcours.Type
    familles = [
        ("Formations", {T.FORMATION}),
        ("Expériences", {T.STAGE, T.EXPERIENCE, T.ASSOCIATION, T.EVENEMENT}),
        ("Certifications", {T.CERTIFICATION}),
    ]
    groupes = [
        (nom, [ligne for ligne in lignes if ligne.type in types]) for nom, types in familles
    ]
    groupes = [groupe for groupe in groupes if groupe[1]]
    return render(request, "portfolio/parcours.html", {"section": section, "groupes": groupes})


def collaborations(request):
    section = section_ou_404("collaborations")
    liste = Collaboration.objects.filter(visible=True).prefetch_related(PROJETS_PUBLIES)
    return render(
        request, "portfolio/collaborations.html", {"section": section, "collaborations": liste}
    )
