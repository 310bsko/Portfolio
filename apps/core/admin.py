from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import PageStatique, ParametresSite, Profil, SectionPublique


class AdminLigneUnique(admin.ModelAdmin):
    """Une seule ligne : la liste mène directement au formulaire."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        objet = self.model.charger()
        meta = self.model._meta
        return HttpResponseRedirect(
            reverse(f"admin:{meta.app_label}_{meta.model_name}_change", args=[objet.pk])
        )


def avertir_sans_alt(request, objet, couples):
    """Avertissement non bloquant : image sans texte alternatif."""
    for champ_image, champ_alt, libelle in couples:
        if getattr(objet, champ_image) and not getattr(objet, champ_alt):
            messages.warning(
                request,
                f"{libelle} : pas de texte alternatif. Le titre sera utilisé à la place.",
            )


@admin.register(Profil)
class ProfilAdmin(AdminLigneUnique):
    fieldsets = [
        ("Identité", {"fields": ["prenom", "nom", "titre", "accroche", "localisation"]}),
        ("Photo", {"fields": ["photo", "photo_alt"]}),
        ("Disponibilité", {"fields": ["disponible", "disponibilite_texte"]}),
        ("Contact et CV", {"fields": ["email_public", "telephone_public", "cv", "cv_anglais"]}),
        (
            "Réseaux",
            {"fields": ["lien_github", "lien_linkedin", "lien_whatsapp", "lien_autre",
                        "lien_autre_libelle"]},
        ),
        ("Logo", {"fields": ["logo_texte", "logo_image", "logo_alt"]}),
        (
            "À propos",
            {"fields": ["apropos_photo", "apropos_photo_alt", "apropos_titre", "apropos_texte"]},
        ),
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        avertir_sans_alt(
            request,
            obj,
            [
                ("photo", "photo_alt", "Photo"),
                ("apropos_photo", "apropos_photo_alt", "Photo de l'À propos"),
                ("logo_image", "logo_alt", "Logo"),
            ],
        )


@admin.register(ParametresSite)
class ParametresSiteAdmin(AdminLigneUnique):
    fieldsets = [
        ("Référencement", {"fields": ["nom_site", "description", "image_partage", "favicon"]}),
        ("Boutons de l'accueil", {"fields": ["bouton_projets", "bouton_contact", "bouton_cv"]}),
        ("Pied de page", {"fields": ["pied_texte", "copyright_debut", "mention_technique"]}),
        ("Contact", {"fields": ["formulaire_actif", "email_notification"]}),
    ]


@admin.register(SectionPublique)
class SectionPubliqueAdmin(admin.ModelAdmin):
    list_display = ["titre", "cle", "sous_titre", "visible", "ordre"]
    list_editable = ["visible", "ordre"]
    readonly_fields = ["cle"]
    fieldsets = [
        (None, {"fields": ["cle", "titre", "sous_titre", "visible", "ordre"]}),
        ("Référencement (facultatif)", {"fields": ["seo_titre", "seo_description"]}),
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PageStatique)
class PageStatiqueAdmin(admin.ModelAdmin):
    list_display = ["titre", "type", "slug", "visible"]
    list_editable = ["visible"]
    fields = ["titre", "slug", "type", "contenu", "visible"]
