# Générateur de kits graphiques — Gefradis

Outil web qui **génère automatiquement des kits de bannières** pour les opérations
commerciales de Gefradis (menuiserie PVC sur-mesure), à destination du métier
marketing — **sans graphiste**.

>  Projet réalisé dans le cadre d'un **test technique** pour une alternance
> *Développeur IA* (Gefradis, groupe Im4Pulse).

##  Objectif

Permettre au marketing de produire, en quelques clics et **à la charte Gefradis**,
l'ensemble des bannières d'une promotion (site web + publicité Google & Meta),
prêtes à déployer.

##  Fonctionnalités

-  Saisie d'un **brief** : mécanique de remise, message commercial, formats souhaités
-  Génération du **texte** des bannières par IA (Claude)
-  **Composition** à la charte (couleurs, police Cabin, logo) aux **dimensions exactes**
-  **Aperçu**, **ajustement** et **régénération** avant export
-  Téléchargement du **kit complet** en `.zip`
-  Formats : site (Header HP desktop/mobile, bandeau catégorie), **Google Display**
  (statique & animé), Google Pmax, Meta

##  Architecture & stack

| Couche | Technologie |
|--------|-------------|
| Backend / API | FastAPI |
| Frontend | HTML/CSS + Tailwind |
| Génération de texte | API Claude (SDK `anthropic`) |
| Composition d'images | HTML/CSS → PNG via Playwright |
| Production (cible) | Cloud Run · Vertex AI · Cloud Storage |

📄 **Conception détaillée** : voir [`docs/conception.pdf`](docs/conception.pdf)
(cahier de conception : besoins, architecture, cas d'utilisation, séquence,
wireframe, plan de construction…).

##  Installation

```powershell
# 1. Créer l'environnement virtuel
python -m venv .venv

# 2. Installer les dépendances
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Configurer la clé API
Copy-Item .env.example .env        # puis renseigner ANTHROPIC_API_KEY dans .env
```

##  Utilisation

```powershell
# Lancer l'application web (depuis la racine du projet)

# Option 1 — simple (comme un app.py Flask)
.\.venv\Scripts\python.exe backend\api.py

# Option 2 — recommandée en développement (rechargement auto du code)
.\.venv\Scripts\python.exe -m uvicorn api:app --app-dir backend --reload
```

Puis ouvrir **http://127.0.0.1:8000** : saisir un brief, générer, ajuster le texte,
puis télécharger le kit en `.zip`.

```powershell
# (optionnel) Tester les briques en ligne de commande
.\.venv\Scripts\python.exe backend/generer_copy.py   # brief -> copy (Claude)
.\.venv\Scripts\python.exe backend/generer_kit.py    # copy -> kit de bannières
```

##  Structure du projet

```
entretient_dev_ia/
├── backend/              # code Python + moteur de rendu
│   ├── api.py            #   API FastAPI (les routes)
│   ├── generer_copy.py   #   rédaction du copy via Claude
│   ├── generer_kit.py    #   composition des bannières via Playwright
│   ├── bannieres/        #   gabarits .j2 (le « moule » des bannières)
│   └── demos/            #   anciens scripts d'apprentissage (archive)
├── frontend/             # interface utilisateur
│   ├── templates/        #   interface.html (la page de l'outil)
│   └── static/           #   CSS/JS maison (Tailwind est en CDN)
├── assets/               # ressources de marque : police Cabin, logo
├── docs/                 # cahier de conception (LaTeX + PDF)
├── output/               # kits générés (ignoré par git)
├── .env.example          # modèle de configuration (clé API)
├── requirements.txt      # dépendances Python
└── README.md
```

##  Statut

 **Fonctionnel de bout en bout** : saisie du brief → génération du texte (Claude) →
composition à la charte → aperçu → ajustement → téléchargement du kit `.zip`. Tous les
formats sont produits, en versions **statique** (PNG) et **animée** (GIF, pour le Display).
Conception détaillée : [`docs/conception.pdf`](docs/conception.pdf). Le déploiement
Cloud Run est prévu en évolution.
