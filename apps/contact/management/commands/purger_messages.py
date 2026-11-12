from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.contact.models import Message


class Command(BaseCommand):
    help = "Supprime les messages de contact de plus de 12 mois."

    def handle(self, *args, **options):
        limite = timezone.now() - timedelta(days=settings.CONTACT_CONSERVATION_JOURS)
        nombre, _ = Message.objects.filter(date__lt=limite).delete()
        self.stdout.write(f"{nombre} message(s) supprimé(s).")
