# Guide d'administration

Tout le contenu du site se modifie depuis l'administration, sans toucher au code.
Une modification est visible sur le site en **moins de 60 secondes**.

Adresse : `https://mon-site/<ADMIN_URL>` (en local : http://127.0.0.1:8000/gestion/).

## Le tableau de bord

La page d'accueil de l'administration affiche :

- les **chiffres clés** (projets publiés, compétences, parcours, collaborations, messages non lus),
  chacun menant à sa liste ;
- les boutons **Ajouter un projet**, **Modifier mon profil** et **Voir le site** ;
- la jauge **Site complété à … %** et la liste de ce qu'il reste à renseigner
  (photo, CV, email public, texte de l'À propos…) : chaque ligne mène au bon formulaire ;
- les **derniers messages** reçus et mes dernières actions.

## Les trois groupes

| Groupe | Ce qu'on y gère |
|---|---|
| **Contenu du site** | Profil, Paramètres du site, Sections du site, Pages |
| **Portfolio** | Projets, Compétences, Catégories, Parcours et certifications, Collaborations |
| **Messages** | Messages reçus par le formulaire de contact |

Règles communes :

- **Seul le nom ou le titre est obligatoire.** Un champ laissé vide n'apparaît pas sur le site.
- **Visible** décoché = masqué (l'élément reste en base et peut être réaffiché).
- **Ordre** : les petits nombres passent en premier. Les colonnes « visible » et « ordre »
  se modifient directement dans les listes (puis bouton **Enregistrer** en bas).
  Ordre à 0 = placé en dernier.
- Les textes longs acceptent le **Markdown** (`**gras**`, `- liste`, `[lien](https://…)`).

## Modifier mon profil

*Contenu du site > Profil* : nom, titre, accroche, photo, disponibilité, email, CV,
réseaux, logo, texte de l'À propos.

- **Photo** : JPEG, PNG ou WebP, 2 Mo au maximum. Elle s'affiche sur l'accueil.
- **Photo de l'À propos** (bloc « À propos ») : une photo différente pour la page À propos.
  Vide = pas de photo sur cette page.
- **CV** : PDF, 4 Mo au maximum. Le bouton « Télécharger mon CV » apparaît dès qu'un CV est envoyé.
- **Logo** : le texte est utilisé si aucune image n'est fournie.

## Paramètres du site

*Contenu du site > Paramètres du site* : nom du site, description (moteurs de recherche),
image de partage, favicon, libellés des trois boutons de l'accueil, pied de page,
activation du formulaire de contact et adresse qui reçoit les notifications.

## Sections et menu

*Contenu du site > Sections du site* : titre, sous-titre, visibilité et ordre de chaque page.
Le menu et le pied de page suivent cet ordre. Une section masquée disparaît du menu et
répond par une page 404. L'accueil ne peut pas être masqué.

## Ajouter un projet

1. *Portfolio > Projets > Ajouter*.
2. Saisir le **titre** (le reste est facultatif).
3. Passer le **statut** à « Publié » pour l'afficher (par défaut : brouillon).
4. Cocher **En vedette** pour l'afficher sur l'accueil (le premier occupe deux colonnes).
5. Ajouter des images de galerie en bas de page si besoin.

Un avertissement jaune signale un projet publié sans résumé ou sans image : ce n'est pas bloquant.

Dans la liste des projets, le menu **Action** permet de publier, passer en brouillon
ou **dupliquer** la sélection. La suppression demande une confirmation.

## Compétences, parcours, collaborations

- **Catégories** : choisir le domaine (projets ou compétences).
  Une compétence sans catégorie apparaît dans « Autres ».
- **Compétence clé** : affichée sur l'accueil.
- **Parcours** : sans date de fin = « aujourd'hui ». Sans date, l'ordre manuel s'applique.
- Supprimer une compétence, une catégorie ou une collaboration ne supprime jamais un projet.

## Pages légales

*Contenu du site > Pages* : mentions légales et politique de confidentialité, en Markdown.
**À relire et compléter avant la mise en ligne** (nom de l'éditeur, contact).

## Messages

*Messages > Messages reçus* : lire, cocher « lu », supprimer.
Les messages de plus de 12 mois sont supprimés automatiquement.

## Sauvegarder

Lien **Exporter les données** en haut à droite de l'administration : un fichier JSON
contenant tout le contenu est téléchargé. À faire avant toute grosse modification.
La restauration est décrite dans le README.

## Compte bloqué ?

Après 5 mots de passe faux, la connexion est bloquée une heure.
Déblocage immédiat depuis mon ordinateur : `uv run python manage.py axes_reset`.
