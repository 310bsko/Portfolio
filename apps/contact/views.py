import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django_ratelimit.core import is_ratelimited

from apps.core.models import ParametresSite
from apps.core.views import section_ou_404

from .forms import FormulaireContact

journal = logging.getLogger(__name__)


def ip_client(group, request):
    """Adresse du visiteur derrière le proxy de l'hébergeur (jamais enregistrée en base)."""
    transmise = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return transmise.split(",")[0].strip() or request.META.get("REMOTE_ADDR", "inconnue")


def notifier(message, destinataire):
    """Prévient le propriétaire par email ; un échec d'envoi ne bloque jamais le visiteur."""
    if not destinataire:
        return
    try:
        EmailMessage(
            subject=f"[Portfolio] {message.sujet or 'Nouveau message'}",
            body=f"De : {message.nom} <{message.email}>\n\n{message.contenu}",
            to=[destinataire],
            reply_to=[message.email],
        ).send()
    except Exception:
        journal.exception("Notification de contact non envoyée")


@never_cache
def contact(request):
    section = section_ou_404("contact")
    parametres = ParametresSite.charger()
    contexte = {
        "section": section,
        "envoye": request.GET.get("envoye") == "1",
        "formulaire": None,
        "trop_de_messages": False,
    }
    if parametres.formulaire_actif:
        formulaire = FormulaireContact(request.POST or None)
        if request.method == "POST":
            if formulaire.est_un_robot:
                # On répond comme si tout allait bien, sans rien enregistrer.
                return redirect(reverse("contact") + "?envoye=1")
            if is_ratelimited(
                request, group="contact", key=ip_client, rate=settings.CONTACT_DEBIT,
                method="POST", increment=True,
            ):
                contexte["trop_de_messages"] = True
            elif formulaire.is_valid():
                message = formulaire.save()
                notifier(message, parametres.email_notification)
                return redirect(reverse("contact") + "?envoye=1")
        contexte["formulaire"] = formulaire
    statut = 429 if contexte["trop_de_messages"] else 200
    return render(request, "contact.html", contexte, status=statut)
