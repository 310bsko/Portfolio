"""Export complet des données (ADM-11), restaurable avec `manage.py loaddata`."""

import io

from django.core.management import call_command


def exporter_donnees(avec_messages=False):
    """Retourne le contenu du site en JSON.

    Les messages de contact (données personnelles de visiteurs) sont exclus par défaut.
    Les fichiers (images, CV) restent sur Cloudinary : seuls leurs chemins sont exportés.
    """
    applications = ["core", "portfolio"] + (["contact"] if avec_messages else [])
    sortie = io.StringIO()
    call_command("dumpdata", *applications, indent=2, stdout=sortie)
    return sortie.getvalue()
