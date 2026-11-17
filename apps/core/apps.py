from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"
    label = "core"
    verbose_name = "Contenu du site"

    def ready(self):
        from django.db.models.signals import post_delete, post_save

        from .donnees import vider_donnees_site
        from .models import PageStatique, ParametresSite, Profil, SectionPublique

        # Une modification dans l'admin vide la mémoire des données communes (donnees.py).
        for modele in (Profil, ParametresSite, SectionPublique, PageStatique):
            nom = modele.__name__
            post_save.connect(vider_donnees_site, sender=modele, dispatch_uid=f"vider-{nom}")
            post_delete.connect(vider_donnees_site, sender=modele, dispatch_uid=f"vider-sup-{nom}")
