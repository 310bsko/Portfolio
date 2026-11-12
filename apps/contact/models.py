from django.db import models


class Message(models.Model):
    """Message reçu par le formulaire de contact. Aucune adresse IP n'est stockée."""

    nom = models.CharField("nom", max_length=100)
    email = models.EmailField("email")
    sujet = models.CharField("sujet", max_length=150, blank=True)
    contenu = models.TextField("message")
    date = models.DateTimeField("reçu le", auto_now_add=True)
    lu = models.BooleanField("lu", default=False)

    class Meta:
        verbose_name = "message"
        verbose_name_plural = "messages reçus"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.nom} — {self.sujet or 'sans sujet'}"
