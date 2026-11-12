"""Contenu général du site : profil, paramètres, sections, pages statiques."""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.urls import reverse
from django.utils.text import slugify

from .fichiers import ChampImage, ChampPDF, Chemin


class Ordonne(models.Model):
    """Ordre manuel : un nouvel élément est placé en dernier."""

    ordre = models.PositiveIntegerField(
        "ordre", default=0, help_text="Les petits nombres passent en premier. 0 = placé en dernier."
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.ordre:
            maximum = type(self).objects.aggregate(m=Max("ordre"))["m"] or 0
            self.ordre = maximum + 1
        super().save(*args, **kwargs)


def slug_unique(instance, texte, champ="slug", longueur=80):
    """Génère un slug lisible et unique pour le modèle de l'instance."""
    base = slugify(texte)[:longueur] or "element"
    slug, numero = base, 2
    modele = type(instance)
    while modele.objects.filter(**{champ: slug}).exclude(pk=instance.pk).exists():
        suffixe = f"-{numero}"
        slug = f"{base[: longueur - len(suffixe)]}{suffixe}"
        numero += 1
    return slug


class LigneUnique(models.Model):
    """Modèle à une seule ligne (identifiant forcé à 1)."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return 0, {}

    @classmethod
    def charger(cls):
        objet, _ = cls.objects.get_or_create(pk=1)
        return objet


class Profil(LigneUnique):
    prenom = models.CharField("prénom", max_length=60, default="Prénom")
    nom = models.CharField("nom", max_length=60, default="Nom")
    titre = models.CharField(
        "titre professionnel", max_length=120, blank=True,
        help_text="Exemple : Ingénieur Data & Cloud Computing",
    )
    accroche = models.TextField(
        "accroche", blank=True, help_text="Une ou deux phrases sous le nom."
    )
    photo = ChampImage("photo", upload_to=Chemin("profil"), blank=True)
    photo_alt = models.CharField("texte alternatif de la photo", max_length=160, blank=True)
    localisation = models.CharField("localisation", max_length=120, blank=True)
    disponible = models.BooleanField(
        "afficher la disponibilité", default=True,
        help_text="Affiche la pastille verte de disponibilité sur l'accueil.",
    )
    disponibilite_texte = models.CharField(
        "texte de disponibilité", max_length=120, blank=True,
        help_text="Exemple : Disponible pour un stage de fin d'études",
    )
    email_public = models.EmailField("email public", blank=True)
    telephone_public = models.CharField("téléphone public", max_length=30, blank=True)
    cv = ChampPDF("CV (PDF)", upload_to=Chemin("cv"), blank=True)
    cv_anglais = ChampPDF("CV anglais (PDF)", upload_to=Chemin("cv"), blank=True)
    lien_github = models.URLField("lien GitHub", blank=True)
    lien_linkedin = models.URLField("lien LinkedIn", blank=True)
    lien_whatsapp = models.URLField(
        "lien WhatsApp", blank=True, help_text="Exemple : https://wa.me/2250700000000"
    )
    lien_autre = models.URLField("autre lien", blank=True)
    lien_autre_libelle = models.CharField("libellé de l'autre lien", max_length=40, blank=True)
    logo_texte = models.CharField(
        "logo (texte)", max_length=40, blank=True,
        help_text="Affiché dans l'en-tête si aucune image de logo n'est fournie. "
        "Vide = prénom et nom.",
    )
    logo_image = ChampImage("logo (image)", upload_to=Chemin("logo"), blank=True)
    logo_alt = models.CharField("texte alternatif du logo", max_length=160, blank=True)
    apropos_photo = ChampImage(
        "photo de l'À propos", upload_to=Chemin("profil"), blank=True,
        help_text="Différente de la photo de l'accueil. Vide = pas de photo sur l'À propos.",
    )
    apropos_photo_alt = models.CharField(
        "texte alternatif de la photo de l'À propos", max_length=160, blank=True
    )
    apropos_titre = models.CharField("titre de l'À propos", max_length=120, blank=True)
    apropos_texte = models.TextField(
        "texte de l'À propos", blank=True, help_text="Texte libre, mis en forme en Markdown."
    )

    class Meta:
        verbose_name = "profil"
        verbose_name_plural = "profil"
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="profil_ligne_unique")]

    def __str__(self):
        return self.nom_complet

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip()

    @property
    def logo(self):
        return self.logo_texte or self.nom_complet

    def clean(self):
        parametres = ParametresSite.objects.filter(pk=1).first()
        if parametres and not parametres.formulaire_actif and not self.email_public:
            raise ValidationError(
                {"email_public": "Le formulaire de contact est désactivé : un email public est "
                 "nécessaire pour qu'il reste un moyen de vous contacter."}
            )


class ParametresSite(LigneUnique):
    nom_site = models.CharField(
        "nom du site", max_length=80, blank=True, help_text="Vide = prénom et nom du profil."
    )
    description = models.TextField(
        "description par défaut", blank=True, max_length=300,
        help_text="Utilisée par les moteurs de recherche et les aperçus de partage.",
    )
    image_partage = ChampImage(
        "image de partage", upload_to=Chemin("site"), blank=True,
        help_text="Image affichée quand le site est partagé (1200 × 630 px conseillé).",
    )
    favicon = ChampImage(
        "favicon", upload_to=Chemin("site"), blank=True, help_text="Image carrée PNG ou WebP."
    )
    pied_texte = models.CharField("texte du pied de page", max_length=200, blank=True)
    copyright_debut = models.PositiveSmallIntegerField(
        "année de début du copyright", null=True, blank=True
    )
    mention_technique = models.CharField(
        "mention technique", max_length=160, blank=True,
        help_text="Exemple : Site réalisé avec Django, hébergé sur Vercel.",
    )
    bouton_projets = models.CharField(
        "bouton « projets »", max_length=40, blank=True, default="Voir mes projets"
    )
    bouton_contact = models.CharField(
        "bouton « contact »", max_length=40, blank=True, default="Me contacter"
    )
    bouton_cv = models.CharField(
        "bouton « CV »", max_length=40, blank=True, default="Télécharger mon CV"
    )
    formulaire_actif = models.BooleanField("formulaire de contact actif", default=True)
    email_notification = models.EmailField(
        "email de notification", blank=True,
        help_text="Adresse qui reçoit un email à chaque message de contact.",
    )

    class Meta:
        verbose_name = "paramètres du site"
        verbose_name_plural = "paramètres du site"
        constraints = [
            models.CheckConstraint(condition=models.Q(id=1), name="parametres_ligne_unique")
        ]

    def __str__(self):
        return "Paramètres du site"

    def clean(self):
        if not self.formulaire_actif:
            profil = Profil.objects.filter(pk=1).first()
            if not (profil and profil.email_public):
                raise ValidationError(
                    {"formulaire_actif": "Au moins un moyen de contact est requis : renseignez "
                     "d'abord un email public dans le profil."}
                )


class SectionPublique(models.Model):
    class Cle(models.TextChoices):
        ACCUEIL = "accueil", "Accueil"
        APROPOS = "apropos", "À propos"
        PROJETS = "projets", "Projets"
        COMPETENCES = "competences", "Compétences"
        PARCOURS = "parcours", "Parcours"
        COLLABORATIONS = "collaborations", "Collaborations"
        CONTACT = "contact", "Contact"

    ROUTES = {
        "accueil": "accueil",
        "apropos": "apropos",
        "projets": "projets",
        "competences": "competences",
        "parcours": "parcours",
        "collaborations": "collaborations",
        "contact": "contact",
    }

    cle = models.CharField("section", max_length=20, choices=Cle.choices, unique=True)
    titre = models.CharField("titre", max_length=80)
    sous_titre = models.CharField("sous-titre", max_length=240, blank=True)
    visible = models.BooleanField("visible", default=True)
    ordre = models.PositiveIntegerField("ordre", default=0)
    seo_titre = models.CharField("titre SEO", max_length=70, blank=True)
    seo_description = models.CharField("description SEO", max_length=300, blank=True)

    class Meta:
        verbose_name = "section du site"
        verbose_name_plural = "sections du site"
        ordering = ["ordre", "id"]

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        if self.cle == self.Cle.ACCUEIL:
            self.visible = True
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(self.ROUTES[self.cle])

    def clean(self):
        if self.cle == self.Cle.ACCUEIL and not self.visible:
            raise ValidationError(
                {"visible": "L'accueil ne peut pas être masqué : c'est la page d'entrée du site."}
            )


class PageStatique(models.Model):
    class Type(models.TextChoices):
        MENTIONS = "mentions", "Mentions légales"
        CONFIDENTIALITE = "confidentialite", "Politique de confidentialité"
        AUTRE = "autre", "Autre"

    titre = models.CharField("titre", max_length=120)
    slug = models.SlugField(
        "adresse", max_length=80, unique=True, blank=True,
        help_text="Générée à partir du titre si laissée vide.",
    )
    type = models.CharField("type", max_length=20, choices=Type.choices, default=Type.AUTRE)
    contenu = models.TextField("contenu", blank=True, help_text="Texte en Markdown.")
    visible = models.BooleanField("visible", default=True)

    class Meta:
        verbose_name = "page"
        verbose_name_plural = "pages"
        ordering = ["titre"]

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unique(self, self.titre)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("page", args=[self.slug])
