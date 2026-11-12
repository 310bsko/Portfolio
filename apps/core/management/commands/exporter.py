from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.sauvegarde import exporter_donnees


class Command(BaseCommand):
    help = "Exporte tout le contenu du site dans un fichier JSON (restauration : loaddata)."

    def add_arguments(self, parser):
        parser.add_argument("--dossier", default="sauvegardes")
        parser.add_argument(
            "--avec-messages", action="store_true",
            help="Inclut les messages de contact (données personnelles).",
        )

    def handle(self, *args, **options):
        dossier = Path(options["dossier"])
        dossier.mkdir(parents=True, exist_ok=True)
        fichier = dossier / f"portfolio-{timezone.localtime():%Y-%m-%d-%H%M}.json"
        fichier.write_text(exporter_donnees(options["avec_messages"]), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Sauvegarde écrite : {fichier}"))
