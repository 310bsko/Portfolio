from django.core.management.base import BaseCommand

from apps.portfolio.models import Categorie, Collaboration, Competence, Parcours, Projet


class Command(BaseCommand):
    help = "Crée un contenu d'exemple pour voir le site rempli en local (à ne pas lancer en ligne)."

    def handle(self, *args, **options):
        if Projet.objects.exists():
            self.stdout.write("Des projets existent déjà : rien n'a été créé.")
            return
        data = Categorie.objects.create(nom="Data", domaine="projet")
        cloud = Categorie.objects.create(nom="Cloud", domaine="projet")
        langages = Categorie.objects.create(nom="Langages", domaine="competence")
        outils = Categorie.objects.create(nom="Cloud et outils", domaine="competence")
        c = {}
        for nom, categorie, niveau, cle in [
            ("Python", langages, "maitrise", True), ("SQL", langages, "maitrise", True),
            ("Django", langages, "utilise", True), ("Airflow", outils, "utilise", True),
            ("Docker", outils, "utilise", True), ("AWS", outils, "notions", True),
            ("Terraform", outils, "notions", False), ("Git", None, "utilise", False),
        ]:
            c[nom] = Competence.objects.create(
                nom=nom, categorie=categorie, niveau=niveau, mise_en_avant=cle
            )
        projets = [
            ("Pipeline de données météo", data, 2026, True, ["Python", "Airflow", "SQL"],
             "Collecte, nettoyage et mise à disposition quotidienne de données météo ouvertes."),
            ("Infrastructure cloud automatisée", cloud, 2026, True, ["AWS", "Terraform", "Docker"],
             "Déploiement reproductible d'une application conteneurisée avec Terraform."),
            ("Tableau de bord des ventes", data, 2025, True, ["Python", "SQL"],
             "Indicateurs clés et visualisations pour suivre l'activité d'une PME."),
            ("Ce portfolio", cloud, 2026, False, ["Django", "Python", "Docker"], ""),
        ]
        for titre, categorie, annee, vedette, technos, resume in projets:
            projet = Projet.objects.create(
                titre=titre, categorie=categorie, annee=annee, mis_en_avant=vedette,
                resume=resume, statut="publie",
                contexte="Projet réalisé dans le cadre de ma formation." if resume else "",
                solution="- Ingestion planifiée\n- Tests automatisés\n- `docker compose up`"
                if resume else "",
            )
            projet.technologies.set([c[nom] for nom in technos])
        Parcours.objects.create(
            titre="Master Data & Cloud Computing", type="formation", organisme="Université",
            lieu="Abidjan", date_debut="2024-09-01",
        )
        Parcours.objects.create(
            titre="Stage Data Engineer", type="stage", organisme="Entreprise",
            date_debut="2025-06-01", date_fin="2025-08-31",
            description="Mise en place d'un pipeline d'ingestion.",
        )
        Parcours.objects.create(titre="AWS Cloud Practitioner", type="certification")
        equipe = Collaboration.objects.create(nom="Équipe projet", role="Camarades de promotion")
        equipe.projets.set(Projet.objects.all()[:2])
        self.stdout.write(self.style.SUCCESS("Contenu d'exemple créé."))
