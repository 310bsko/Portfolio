"""Site d'administration : groupes dans l'ordre du cahier des charges et export en un clic."""

from django.contrib import admin
from django.contrib.admin.apps import AdminConfig
from django.http import HttpResponse
from django.urls import path, reverse
from django.utils import timezone

ORDRE = {
    "core": ["Profil", "ParametresSite", "SectionPublique", "PageStatique"],
    "portfolio": ["Projet", "Competence", "Categorie", "Parcours", "Collaboration"],
    "contact": ["Message"],
}


def _rang(liste, valeur):
    return liste.index(valeur) if valeur in liste else len(liste)


class AdminPortfolio(admin.AdminSite):
    site_header = "Administration du portfolio"
    site_title = "Portfolio"
    index_title = "Tableau de bord"

    def get_app_list(self, request, app_label=None):
        applications = super().get_app_list(request, app_label)
        ordre_apps = list(ORDRE)
        applications.sort(key=lambda app: _rang(ordre_apps, app["app_label"]))
        for app in applications:
            modeles = ORDRE.get(app["app_label"], [])
            app["models"].sort(key=lambda m: _rang(modeles, m["object_name"]))
        return applications

    def index(self, request, extra_context=None):
        """Tableau de bord : chiffres clés, raccourcis, points à compléter, derniers messages."""
        from apps.contact.models import Message
        from apps.portfolio.models import Collaboration, Competence, Parcours, Projet

        from .models import ParametresSite, Profil

        profil = Profil.charger()
        parametres = ParametresSite.charger()
        publies = Projet.objects.publies().count()
        brouillons = Projet.objects.count() - publies
        non_lus = Message.objects.filter(lu=False).count()

        def lien(nom, *args):
            return reverse(f"admin:{nom}", args=args)

        chiffres = [
            ("Projets publiés", publies, f"{brouillons} en brouillon",
             lien("portfolio_projet_changelist")),
            ("Compétences", Competence.objects.filter(visible=True).count(), "visibles",
             lien("portfolio_competence_changelist")),
            ("Parcours", Parcours.objects.filter(visible=True).count(), "lignes visibles",
             lien("portfolio_parcours_changelist")),
            ("Collaborations", Collaboration.objects.filter(visible=True).count(), "visibles",
             lien("portfolio_collaboration_changelist")),
            ("Messages non lus", non_lus, f"sur {Message.objects.count()} reçus",
             lien("contact_message_changelist") + "?lu__exact=0"),
        ]
        url_profil = lien("core_profil_change", profil.pk)
        url_parametres = lien("core_parametressite_change", parametres.pk)
        controles = [
            (bool(profil.photo), "Ajouter une photo de profil", url_profil),
            (bool(profil.titre), "Renseigner le titre professionnel", url_profil),
            (bool(profil.apropos_texte), "Rédiger le texte de l'À propos", url_profil),
            (bool(profil.cv), "Envoyer le CV en PDF", url_profil),
            (bool(profil.email_public), "Indiquer un email public", url_profil),
            (bool(profil.lien_github or profil.lien_linkedin), "Ajouter GitHub ou LinkedIn",
             url_profil),
            (publies > 0, "Publier un premier projet", lien("portfolio_projet_add")),
            (bool(parametres.description), "Écrire la description du site (SEO)", url_parametres),
            (bool(parametres.email_notification), "Indiquer l'email de notification",
             url_parametres),
        ]
        a_faire = [(texte, url) for fait, texte, url in controles if not fait]
        contexte = {
            "chiffres": chiffres,
            "a_faire": a_faire,
            "avancement": round(100 * (len(controles) - len(a_faire)) / len(controles)),
            "derniers_messages": Message.objects.all()[:5],
            "url_profil": url_profil,
            "url_parametres": url_parametres,
            **(extra_context or {}),
        }
        return super().index(request, contexte)

    def get_urls(self):
        return [
            path("exporter/", self.admin_view(self.exporter), name="exporter"),
        ] + super().get_urls()

    def exporter(self, request):
        from .sauvegarde import exporter_donnees

        contenu = exporter_donnees(avec_messages=request.GET.get("messages") == "1")
        nom = f"portfolio-{timezone.localtime():%Y-%m-%d-%H%M}.json"
        reponse = HttpResponse(contenu, content_type="application/json; charset=utf-8")
        reponse["Content-Disposition"] = f'attachment; filename="{nom}"'
        return reponse


class AdminPortfolioConfig(AdminConfig):
    default_site = "apps.core.site_admin.AdminPortfolio"
