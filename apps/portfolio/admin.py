from django.contrib import admin, messages

from apps.core.admin import avertir_sans_alt

from .models import Categorie, Collaboration, Competence, Parcours, Projet, ProjetImage


@admin.action(description="Afficher la sélection")
def afficher(modeladmin, request, queryset):
    queryset.update(visible=True)


@admin.action(description="Masquer la sélection")
def masquer(modeladmin, request, queryset):
    queryset.update(visible=False)


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ["nom", "domaine", "visible", "ordre"]
    list_editable = ["visible", "ordre"]
    list_filter = ["domaine"]
    fields = ["nom", "domaine", "slug", "visible", "ordre"]
    actions = [afficher, masquer]


@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ["nom", "categorie", "niveau", "mise_en_avant", "visible", "ordre"]
    list_editable = ["mise_en_avant", "visible", "ordre"]
    list_filter = ["categorie", "niveau", "visible"]
    search_fields = ["nom"]
    fields = ["nom", "categorie", "niveau", "icone", "mise_en_avant", "visible", "ordre"]
    actions = [afficher, masquer]


class ProjetImageInline(admin.TabularInline):
    model = ProjetImage
    extra = 1
    fields = ["image", "alt", "legende", "ordre"]


@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    list_display = ["titre", "categorie", "annee", "statut", "mis_en_avant", "ordre"]
    list_editable = ["statut", "mis_en_avant", "ordre"]
    list_filter = ["statut", "categorie", "mis_en_avant"]
    search_fields = ["titre", "resume"]
    filter_horizontal = ["technologies"]
    inlines = [ProjetImageInline]
    actions = ["publier", "mettre_en_brouillon", "dupliquer"]
    fieldsets = [
        (None, {"fields": ["titre", "statut", "mis_en_avant", "resume"]}),
        ("Image de couverture", {"fields": ["image", "image_alt"]}),
        ("Classement", {"fields": ["categorie", "technologies", "annee", "ordre", "slug"]}),
        ("Liens", {"fields": ["lien_github", "lien_demo"]}),
        (
            "Présentation détaillée (Markdown, tout est facultatif)",
            {"fields": ["contexte", "problematique", "solution", "role", "resultats"]},
        ),
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.est_publie:
            manques = [
                nom for nom, valeur in [("résumé", obj.resume), ("image", obj.image)] if not valeur
            ]
            if manques:
                messages.warning(
                    request,
                    f"Projet publié sans {' ni '.join(manques)} : il s'affiche quand même, "
                    "mais il sera plus convaincant une fois complété.",
                )
        avertir_sans_alt(request, obj, [("image", "image_alt", "Image de couverture")])

    @admin.action(description="Publier la sélection")
    def publier(self, request, queryset):
        queryset.update(statut=Projet.Statut.PUBLIE)

    @admin.action(description="Passer la sélection en brouillon (masquer)")
    def mettre_en_brouillon(self, request, queryset):
        queryset.update(statut=Projet.Statut.BROUILLON)

    @admin.action(description="Dupliquer la sélection (copie en brouillon)")
    def dupliquer(self, request, queryset):
        for projet in queryset:
            technologies = list(projet.technologies.all())
            collaborations = list(projet.collaborations.all())
            images = list(projet.images.all())
            projet.pk = None
            projet._state.adding = True
            projet.titre = f"{projet.titre} (copie)"[:120]
            projet.slug = ""
            projet.ordre = 0
            projet.statut = Projet.Statut.BROUILLON
            projet.mis_en_avant = False
            projet.save()
            projet.technologies.set(technologies)
            projet.collaborations.set(collaborations)
            for image in images:
                image.pk = None
                image._state.adding = True
                image.projet = projet
                image.save()
        messages.success(request, "Copie créée en brouillon.")


@admin.register(Parcours)
class ParcoursAdmin(admin.ModelAdmin):
    list_display = ["titre", "type", "organisme", "date_debut", "date_fin", "visible", "ordre"]
    list_editable = ["visible", "ordre"]
    list_filter = ["type", "visible"]
    search_fields = ["titre", "organisme"]
    fields = ["titre", "type", "organisme", "lieu", "date_debut", "date_fin", "description",
              "lien", "logo", "visible", "ordre"]
    actions = [afficher, masquer]


@admin.register(Collaboration)
class CollaborationAdmin(admin.ModelAdmin):
    list_display = ["nom", "role", "organisation", "visible", "ordre"]
    list_editable = ["visible", "ordre"]
    search_fields = ["nom", "organisation"]
    filter_horizontal = ["projets"]
    fields = ["nom", "role", "organisation", "logo", "lien", "projets", "visible", "ordre"]
    actions = [afficher, masquer]
