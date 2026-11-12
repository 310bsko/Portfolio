# Portfolio d'étudiant (Django)

Site de portfolio **entièrement administrable sans toucher au code**, en français,
pour un coût d'exploitation de 0 FCFA. Référence : cahier des charges V3.3.

- Pages publiques : accueil, à propos, projets (liste, filtre, détail), compétences,
  parcours, collaborations, contact, pages légales, 404 et 500.
- Administration privée : profil, paramètres, sections, pages, projets, compétences,
  catégories, parcours, collaborations, messages, export en un clic.
- Guide d'utilisation de l'administration : [docs/guide-administration.md](docs/guide-administration.md).

## Lancer le site en local

Il faut Python 3.12 ou plus récent et [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                   # installe les dépendances
cp .env.example .env                      # réglages locaux (DEBUG=True)
uv run python manage.py migrate           # crée la base SQLite et le contenu de départ
uv run python manage.py createcachetable  # cache partagé (anti-spam)
uv run python manage.py createsuperuser   # mon compte administrateur
uv run python manage.py runserver
```

- Site : http://127.0.0.1:8000/
- Administration : http://127.0.0.1:8000/gestion/ (adresse réglable avec `ADMIN_URL`)

Pour voir le site rempli avec un contenu d'exemple (en local seulement) :

```bash
uv run python manage.py contenu_demo
```

En local, la base est un fichier SQLite, les images vont dans `media/` et les emails
s'affichent dans la console.

## Vérifier le code

```bash
uv run pytest          # tests des règles de gestion
uv run ruff check .    # qualité du code
```

## Mettre en ligne (Vercel + Neon + Cloudinary)

1. **GitHub** : créer un dépôt et y pousser ce dossier.
2. **Neon** : créer un projet, copier l'adresse de connexion **« pooled »**.
3. **Cloudinary** : créer un compte, copier la variable `CLOUDINARY_URL`.
   Dans *Settings > Security*, cocher **« Allow delivery of PDF and ZIP files »**
   (sinon le CV ne se télécharge pas).
4. **Vercel** : importer le dépôt (offre Hobby) et définir ces variables d'environnement
   **avant** le premier déploiement :

| Variable | Valeur |
|---|---|
| `SECRET_KEY` | une longue chaîne aléatoire (commande ci-dessous) |
| `DATABASE_URL` | l'adresse « pooled » de Neon |
| `CLOUDINARY_URL` | `cloudinary://CLE:SECRET@NOM_DU_CLOUD` |
| `ADMIN_URL` | une adresse que moi seul connais, par exemple `mon-espace-prive/` |
| `ALLOWED_HOSTS` | facultatif : `*.vercel.app` est déjà accepté |
| `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | facultatif : notification par email (voir `.env.example` pour Resend) |

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

Vercel détecte Django grâce à `manage.py`, lance la commande de build déclarée dans
`pyproject.toml` (`migrate` puis `createcachetable`), puis `collectstatic`, et sert les
fichiers statiques depuis son CDN.

5. **Créer le compte administrateur** dans la base Neon, depuis mon ordinateur
   (remplacer les valeurs ; ne jamais les enregistrer dans le dépôt) :

```bash
DATABASE_URL="adresse-neon" SECRET_KEY="la-meme-cle" uv run python manage.py createsuperuser
```

### Liste de contrôle du prototype (cahier des charges, 6.4)

- [ ] la page d'accueil s'affiche, avec les polices et la mise en page ;
- [ ] durée du premier chargement après une pause (réveil) : ……… secondes ;
- [ ] connexion à l'administration, puis déconnexion ;
- [ ] ajout d'un projet publié : il apparaît sur le site en moins de 60 secondes, sans redéployer ;
- [ ] envoi d'une image depuis l'administration : elle s'affiche (Cloudinary) ;
- [ ] envoi du CV en PDF : il se télécharge depuis l'accueil ;
- [ ] un message de contact arrive dans l'administration (et par email si configuré) ;
- [ ] cinq mots de passe faux : la connexion est bloquée pendant une heure.

Si un point échoue, le noter avant d'aller plus loin : le repli prévu est Render
(le `Dockerfile` est prêt).

## Sauvegarde et restauration

- **En un clic** : lien « Exporter les données » en haut de l'administration.
- **En commande** : `uv run python manage.py exporter` (fichier dans `sauvegardes/`).
- **Planifiée** : `.github/workflows/backup.yml`, chaque lundi (secrets `DATABASE_URL`
  et `SECRET_KEY` à créer dans GitHub). À vérifier une fois par mois : GitHub désactive
  les tâches planifiées après 60 jours sans activité sur le dépôt.
- **Restaurer** : `uv run python manage.py loaddata sauvegardes/portfolio-AAAA-MM-JJ-HHMM.json`

Les messages de contact ne sont pas dans les sauvegardes (données personnelles) ;
ils sont supprimés après 12 mois par `manage.py purger_messages`.
Les fichiers (images, CV) restent sur Cloudinary : la sauvegarde contient leurs chemins.

## Sécurité

- Connexion bloquée une heure après 5 mots de passe faux (déblocage : `manage.py axes_reset`).
- Déconnexion automatique après 30 minutes d'inactivité.
- Formulaire de contact : champ piège, 5 messages par heure et par adresse IP au maximum.
- Images : JPEG, PNG ou WebP de 2 Mo au plus, type réel vérifié, métadonnées supprimées,
  noms régénérés ; SVG refusé. CV : vrai PDF de 4 Mo au plus.

## Organisation du code

```
config/          réglages (un seul fichier), adresses, WSGI
apps/core/       profil, paramètres, sections, pages, fichiers, stockage Cloudinary, export
apps/portfolio/  projets, galerie, compétences, catégories, parcours, collaborations
apps/contact/    formulaire de contact et messages reçus
templates/       gabarits HTML (aucun contenu éditorial)
static/          CSS, un petit script d'animation, polices Inter et Outfit
tests/           tests pytest
docs/            guide d'administration
```

Façon de travailler : une branche par évolution, fusion dans `main` seulement si la CI
est verte. Vercel déploie `main` automatiquement.
