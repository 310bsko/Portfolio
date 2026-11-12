"""Portfolio : projets, galerie, compétences, catégories, parcours, collaborations.

Règle D6 : seul le nom ou le titre est obligatoire ; tout le reste est facultatif.
"""

from django.db import models
from django.db.models import F
from django.urls import reverse

from apps.core.fichiers import ChampImage, Chemin
from apps.core.models import Ordonne, slug_unique


class Categorie(Ordonne):
    class Domaine(models.TextChoices):
        PROJET = "projet", "Projets"
        COMPETENCE = "competence", "Compétences"

    nom = models.CharField("nom", max_length=80)
    slug = models.SlugField("adresse", max_length=80, unique=True, blank=True)
    domaine = models.CharField(
        "domaine", max_length=12, choices=Domaine.choices, default=Domaine.PROJET
    )
    visible = models.BooleanField("visible", default=True)

    class Meta:
        verbose_name = "catégorie"
        verbose_name_plural = "catégories"
        ordering = ["domaine", "ordre", "nom"]

    def __str__(self):
        return f"{self.nom} ({self.get_domaine_display().lower()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unique(self, self.nom)
        super().save(*args, **kwargs)


class CompetenceQuerySet(models.QuerySet):
    def publiques(self):
        """Compétences visibles, hors catégories masquées (sans catégorie = « Autres »)."""
        return self.filter(visible=True).filter(
            models.Q(categorie__isnull=True) | models.Q(categorie__visible=True)
        )


class Competence(Ordonne):
    class Niveau(models.TextChoices):
        NOTIONS = "notions", "Notions"
        UTILISE = "utilise", "Utilisé"
        MAITRISE = "maitrise", "Maîtrisé"

    nom = models.CharField("nom", max_length=80)
    categorie = models.ForeignKey(
        Categorie, verbose_name="catégorie", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="competences",
        limit_choices_to={"domaine": Categorie.Domaine.COMPETENCE},
        help_text="Sans catégorie, la compétence apparaît dans le groupe « Autres ».",
    )
    niveau = models.CharField("niveau", max_length=10, choices=Niveau.choices, blank=True)
    icone = ChampImage("icône", upload_to=Chemin("competences"), blank=True)
    mise_en_avant = models.BooleanField(
        "compétence clé", default=False, help_text="Affichée sur la page d'accueil."
    )
    visible = models.BooleanField("visible", default=True)

    objects = CompetenceQuerySet.as_manager()

    class Meta:
        verbose_name = "compétence"
        verbose_name_plural = "compétences"
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom


class ProjetQuerySet(models.QuerySet):
    def publies(self):
        return self.filter(statut=Projet.Statut.PUBLIE)


class Projet(Ordonne):
    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        PUBLIE = "publie", "Publié"

    titre = models.CharField("titre", max_length=120)
    slug = models.SlugField(
        "adresse", max_length=80, unique=True, blank=True,
        help_text="Générée à partir du titre si laissée vide.",
    )
    resume = models.TextField("résumé", blank=True, max_length=300)
    contexte = models.TextField("contexte", blank=True, help_text="Markdown.")
    problematique = models.TextField("problématique", blank=True, help_text="Markdown.")
    solution = models.TextField("solution", blank=True, help_text="Markdown.")
    role = models.TextField("mon rôle", blank=True, help_text="Markdown.")
    resultats = models.TextField("résultats", blank=True, help_text="Markdown.")
    image = ChampImage("image de couverture", upload_to=Chemin("projets"), blank=True)
    image_alt = models.CharField("texte alternatif de l'image", max_length=160, blank=True)
    categorie = models.ForeignKey(
        Categorie, verbose_name="catégorie", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="projets",
        limit_choices_to={"domaine": Categorie.Domaine.PROJET},
    )
    technologies = models.ManyToManyField(
        Competence, verbose_name="technologies", blank=True, related_name="projets"
    )
    annee = models.PositiveSmallIntegerField("année", null=True, blank=True)
    lien_github = models.URLField("lien GitHub", blank=True)
    lien_demo = models.URLField("lien démo", blank=True)
    mis_en_avant = models.BooleanField(
        "en vedette", default=False, help_text="Affiché sur la page d'accueil."
    )
    statut = models.CharField(
        "statut", max_length=10, choices=Statut.choices, default=Statut.BROUILLON
    )

    objects = ProjetQuerySet.as_manager()

    class Meta:
        verbose_name = "projet"
        verbose_name_plural = "projets"
        ordering = ["ordre", "-id"]

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unique(self, self.titre)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("projet", args=[self.slug])

    @property
    def est_publie(self):
        return self.statut == self.Statut.PUBLIE

    @property
    def alt(self):
        return self.image_alt or self.titre


class ProjetImage(Ordonne):
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name="images")
    image = ChampImage("image", upload_to=Chemin("projets/galerie"))
    alt = models.CharField("texte alternatif", max_length=160, blank=True)
    legende = models.CharField("légende", max_length=200, blank=True)

    class Meta:
        verbose_name = "image de galerie"
        verbose_name_plural = "galerie (images et schémas)"
        ordering = ["ordre", "id"]

    def __str__(self):
        return self.legende or f"Image {self.pk}"


class ParcoursQuerySet(models.QuerySet):
    def chronologie(self):
        """Du plus récent au plus ancien ; sans date, l'ordre manuel s'applique."""
        return self.order_by(F("date_debut").desc(nulls_last=True), "ordre", "id")


class Parcours(Ordonne):
    class Type(models.TextChoices):
        FORMATION = "formation", "Formation"
        STAGE = "stage", "Stage"
        EXPERIENCE = "experience", "Expérience"
        ASSOCIATION = "association", "Association"
        EVENEMENT = "evenement", "Événement"
        CERTIFICATION = "certification", "Certification"

    titre = models.CharField("titre", max_length=140)
    type = models.CharField("type", max_length=15, choices=Type.choices)
    organisme = models.CharField("organisme", max_length=140, blank=True)
    lieu = models.CharField("lieu", max_length=120, blank=True)
    date_debut = models.DateField("date de début", null=True, blank=True)
    date_fin = models.DateField(
        "date de fin", null=True, blank=True, help_text="Laisser vide si c'est en cours."
    )
    description = models.TextField("description", blank=True, help_text="Markdown.")
    lien = models.URLField("lien de vérification", blank=True)
    logo = ChampImage("logo", upload_to=Chemin("parcours"), blank=True)
    visible = models.BooleanField("visible", default=True)

    objects = ParcoursQuerySet.as_manager()

    class Meta:
        verbose_name = "ligne de parcours"
        verbose_name_plural = "parcours et certifications"
        ordering = ["ordre", "id"]

    def __str__(self):
        return self.titre


class Collaboration(Ordonne):
    nom = models.CharField("nom", max_length=120, help_text="Personne ou organisation.")
    role = models.CharField("rôle", max_length=140, blank=True)
    organisation = models.CharField("organisation", max_length=140, blank=True)
    logo = ChampImage("logo ou photo", upload_to=Chemin("collaborations"), blank=True)
    lien = models.URLField("lien", blank=True)
    projets = models.ManyToManyField(
        Projet, verbose_name="projets liés", blank=True, related_name="collaborations"
    )
    visible = models.BooleanField("visible", default=True)

    class Meta:
        verbose_name = "collaboration"
        verbose_name_plural = "collaborations"
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom
