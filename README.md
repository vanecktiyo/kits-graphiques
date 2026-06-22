# Générateur de kits graphiques · Gefradis

Outil web qui **génère automatiquement des kits de bannières** pour les opérations
commerciales de Gefradis (menuiserie PVC sur-mesure), à destination du métier marketing,
**sans graphiste**.

> Projet réalisé dans le cadre d'un **test technique** pour une alternance
> *Développeur IA* (Gefradis, groupe Im4Pulse).

🔗 **Application en ligne :** https://gefradis-kits-569401851333.europe-west9.run.app

## Objectif

Permettre au marketing de produire, en quelques clics et **à la charte Gefradis**,
l'ensemble des bannières d'une opération commerciale (site web + publicité Google & Meta),
aux dimensions exactes et prêtes à déployer.

## Fonctionnalités

- Saisie d'un **brief** : mécanique de remise, message commercial, image, formats souhaités
- Génération du **texte** des bannières par IA (Claude), renvoyé en **JSON structuré**
- **Composition** à la charte (couleurs, police Cabin, logo) aux **dimensions exactes**
- **Aperçu**, **ajustement à la main** (sans rappeler l'IA) et **régénération** avant export
- Téléchargement du **kit complet** en `.zip`
- Formats : site (Header HP desktop/mobile, bandeau catégorie), **Google Display**
  (statique & animé GIF), Google Pmax, Meta

## Deux approches explorées

Deux moteurs de montage ont été construits et comparés :

- **A** : gabarits figés (un modèle HTML par type de bannière).
- **B** : gabarit composable unique. Une seule trame adaptative ; le code calcule une
  **disposition** par format (centré, côte à côte, empilé, bandeau…) et met le contenu
  **à l'échelle** pour qu'il remplisse l'espace sans jamais déborder.

La version **B a été retenue et déployée** : plus générique, elle s'adapte à n'importe
quel brief et n'importe quel format. C'est elle qui tourne en ligne.

## Principe clé

> **L'IA rédige le texte ; le code compose et rend l'image.**

Claude ne produit jamais de HTML : il renvoie seulement un **JSON** (accroche, sous-titre,
offre, paliers, date…). Le code place ces données dans le gabarit de la charte, puis
**Playwright (Chromium)** « photographie » le résultat en PNG. Résultat : aucun risque de
HTML cassé, de charte non respectée ou de mauvaise dimension.

## Architecture & stack

| Couche | Technologie |
|--------|-------------|
| Backend / API | FastAPI |
| Frontend | HTML/CSS + Tailwind |
| Génération de texte | API Claude (SDK `anthropic`, tool use → JSON) |
| Composition d'images | HTML/CSS → PNG via Playwright (Chromium) |
| Conteneurisation | Docker |
| Production | **Cloud Run** + Secret Manager (clé) + Cloud Storage (sorties) |
| Intégration continue | **CI/CD** via Cloud Build (push → build → déploiement auto) |

📄 **Conception détaillée** : [`docs/conception.pdf`](docs/conception.pdf)
(besoins, architecture, cas d'utilisation, séquence, déploiement…).

## Installation (local)

```powershell
# 1. Environnement virtuel
python -m venv .venv

# 2. Dépendances
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium

# 3. Clé API : créer un fichier .env à la racine contenant
#    ANTHROPIC_API_KEY=sk-...
```

## Utilisation (local)

```powershell
# Lancer la version déployée (B, composable) depuis la racine du projet
.\.venv\Scripts\python.exe composable\backend\api.py
```

Puis ouvrir **http://127.0.0.1:8001** : saisir un brief, générer, ajuster le texte,
puis télécharger le kit en `.zip`.

```powershell
# (optionnel) tester les briques en ligne de commande
.\.venv\Scripts\python.exe composable\backend\generer_copy.py   # brief -> copy (Claude)
.\.venv\Scripts\python.exe composable\backend\generer_kit.py    # copy -> kit de bannières
```

## Déploiement

L'application est conteneurisée (Docker) et déployée sur **Google Cloud Run** :

- image stockée dans **Artifact Registry** ;
- clé API fournie par **Secret Manager** (jamais dans le code ni l'image) ;
- bannières générées écrites dans **Cloud Storage** (bucket partagé entre instances) ;
- **CI/CD** : à chaque `git push` sur `main`, **Cloud Build** reconstruit l'image et
  redéploie automatiquement (recette dans [`cloudbuild.yaml`](cloudbuild.yaml)).

## Structure du projet

```
kits-graphiques/
├── composable/              # VERSION B (déployée) — gabarit composable unique
│   ├── backend/
│   │   ├── api.py             #   API FastAPI (port 8001)
│   │   ├── generer_copy.py    #   brief -> copy JSON via Claude
│   │   ├── generer_kit.py     #   copy -> bannières via Playwright
│   │   └── bannieres/         #   gabarit .j2 (composable)
│   ├── frontend/templates/    #   interface.html
│   └── assets/                #   police Cabin, logo, images produit
├── backend/, frontend/      # VERSION A (gabarits figés) — exploration
├── docs/                    # cahier de conception + notes (LaTeX + PDF)
├── Dockerfile               # image de production (Python + Chromium)
├── cloudbuild.yaml          # recette CI/CD (Cloud Build)
├── requirements.txt
└── README.md
```

## Statut

✅ **En production** : l'application est **déployée et accessible en ligne**, avec un
**CI/CD** opérationnel. De bout en bout : brief → texte (Claude) → composition à la charte
→ aperçu → ajustement → kit `.zip`. Tous les formats sont produits, en **statique** (PNG)
et **animé** (GIF, pour le Display).
