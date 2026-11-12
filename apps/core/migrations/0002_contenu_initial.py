"""Contenu de départ : tout est ensuite modifiable depuis l'administration."""

from django.db import migrations

SECTIONS = [
    ("accueil", "Accueil", ""),
    ("apropos", "À propos", "Qui je suis, ce que je cherche."),
    ("projets", "Projets", "Ce que j'ai conçu, construit et déployé."),
    ("competences", "Compétences", "Les outils et les méthodes que j'utilise."),
    ("parcours", "Parcours", "Formations, expériences et certifications."),
    ("collaborations", "Collaborations", "Les personnes et organisations avec qui j'ai travaillé."),
    ("contact", "Contact", "Une question, une offre de stage ? Écrivez-moi."),
]

MENTIONS = """## Éditeur du site

Ce site est le portfolio personnel de son auteur. Il est édité à titre non commercial.

## Hébergement

Le site est hébergé par Vercel Inc. Les fichiers sont stockés chez Cloudinary et la base
de données chez Neon.

## Propriété intellectuelle

Les textes, images et projets présentés sont la propriété de leur auteur, sauf mention contraire.
"""

CONFIDENTIALITE = """## Données collectées

Ce site ne dépose aucun cookie de suivi et n'utilise aucun outil de statistiques.

Seul le **formulaire de contact** collecte des données : votre nom, votre adresse email,
le sujet et le contenu de votre message. Aucune adresse IP n'est enregistrée.

## Utilisation et conservation

Ces données servent uniquement à vous répondre. Elles sont conservées **12 mois au maximum**,
puis supprimées. Elles ne sont jamais transmises à des tiers.

## Vos droits

Vous pouvez demander la consultation ou la suppression de vos données en écrivant
par le formulaire de contact.
"""


def creer(apps, schema_editor):
    Profil = apps.get_model("core", "Profil")
    Parametres = apps.get_model("core", "ParametresSite")
    Section = apps.get_model("core", "SectionPublique")
    Page = apps.get_model("core", "PageStatique")

    Profil.objects.get_or_create(
        pk=1,
        defaults={
            "prenom": "Soumaila",
            "nom": "BAKAYOKO",
            "titre": "Ingénierie Data & Cloud Computing",
            "accroche": "Étudiant en fin d'études, je conçois des pipelines de données "
            "et des architectures cloud fiables. Je cherche un stage.",
            "disponible": True,
            "disponibilite_texte": "Disponible pour un stage",
            "apropos_titre": "Quelques mots sur moi",
        },
    )
    Parametres.objects.get_or_create(
        pk=1,
        defaults={
            "description": "Portfolio d'un étudiant en ingénierie Data et Cloud Computing : "
            "projets, compétences, parcours et contact.",
            "mention_technique": "Site réalisé avec Django.",
        },
    )
    for ordre, (cle, titre, sous_titre) in enumerate(SECTIONS, start=1):
        Section.objects.get_or_create(
            cle=cle, defaults={"titre": titre, "sous_titre": sous_titre, "ordre": ordre}
        )
    Page.objects.get_or_create(
        slug="mentions-legales",
        defaults={"titre": "Mentions légales", "type": "mentions", "contenu": MENTIONS},
    )
    Page.objects.get_or_create(
        slug="confidentialite",
        defaults={
            "titre": "Politique de confidentialité",
            "type": "confidentialite",
            "contenu": CONFIDENTIALITE,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunPython(creer, migrations.RunPython.noop)]
