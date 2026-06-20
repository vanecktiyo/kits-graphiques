# Plan de mise en production (déploiement GCP) — tâches à faire

Feuille de route pour passer du prototype à une application **professionnelle, conforme au
cahier des charges, déployable sur Google Cloud Platform**.

Principe directeur (validé par l'état de l'art, voir [etat_de_l_art.md](etat_de_l_art.md)) :
**garder le cœur déterministe** (brief → Claude renvoie du JSON structuré → gabarits HTML/CSS
à charte figée → rendu image). On ne laisse jamais le modèle générer les pixels ni le HTML.

Légende : ⬜ à faire · 🔄 en cours · ✅ fait

---

## Phase 0 — Décisions

- ⬜ **Choisir la version finale.** Reco : finaliser **la version A** comme produit livrable
  (elle porte les dernières décisions : menu image, champ bouton, règle « -X% dans le coin »,
  rendu 2x), et **garder B comme alternative composable documentée** pour l'oral. Éviter de
  re-synchroniser B juste avant l'échéance (moins de risque).
- ⬜ Geler le périmètre v1 (ce qui doit marcher pour le test) vs v2 (améliorations).

## Phase 1 — Cœur applicatif (déjà en place, à consolider)

- ✅ Pipeline : brief → `generer_copy` (JSON via tool use) → `generer_kit` (gabarits) → rendu
  Playwright → kit multi-formats + zip.
- ✅ Charte figée dans les gabarits (couleurs, police Cabin, formes), JSON jamais en HTML.
- ⬜ Finir la passe de QA sur tous les briefs (cf. [problemes_comparaison.md](problemes_comparaison.md)).
- ⬜ Nettoyer les fichiers morts de A (`banniere_pub_large.html.j2`, `banniere.html.j2`).

## Phase 2 — Mise en production GCP

- ⬜ **Conteneuriser (Docker).** Image Python + Playwright/Chromium avec dépendances système
  (`playwright install --with-deps chromium`) + police Cabin embarquée. Tester le rendu en local
  dans le conteneur.
- ⬜ **Déployer sur Cloud Run.** Mémoire ≥ 1–2 Go (Chromium gourmand), CPU 1–2, **timeout** de
  requête augmenté, **concurrency basse** par instance (1–4, éviter d'empiler plusieurs Chromium),
  min-instances = 1 si on veut éviter les démarrages à froid. Scale-to-zero quand inactif.
- ⬜ **Secret Manager** pour `ANTHROPIC_API_KEY` (jamais dans l'image ni le dépôt), injectée en
  variable d'environnement.
- ⬜ **Sorties sur Cloud Storage (GCS).** Le disque Cloud Run est éphémère : écrire PNG/GIF/zip
  dans un **bucket** et servir via URL signée, au lieu d'écrire en local comme aujourd'hui.
- ⬜ **Claude via Vertex AI.** Basculer l'appel modèle sur **Vertex AI (Model Garden)** pour une
  appli GCP-native : IAM, facturation et logs unifiés sur GCP, meilleure conformité/résidence des
  données. (Garder l'API Anthropic directe comme repli.)
- ⬜ **Observabilité.** Cloud Logging + Error Reporting.
- ⬜ **CI/CD.** Cloud Build → Artifact Registry → Cloud Run (déploiement automatisé).
- ⬜ (si gros volumes un jour) File de jobs via Cloud Tasks / Pub/Sub. Pour le test, Cloud Run seul
  suffit.

## Phase 3 — Améliorations IA (optionnelles, fort effet à l'oral)

- ⬜ **Relecture qualité visuelle (agent réflexif, style MIMO), bornée et optionnelle.** Après le
  rendu, renvoyer le PNG à Claude (vision) avec les règles de charte : « le texte déborde-t-il ?
  le logo chevauche-t-il le titre ? lisibilité et charte OK ? » → réponse JSON (ok / problèmes /
  correctifs). Si problème, réajuster et re-rendre (1–2 passes max). À déclencher à la demande
  (bouton « Vérifier la qualité »), pas sur chaque génération (coût/latence).
- ⬜ **Choix intelligent de l'image produit** par Claude (vision) : lui montrer les miniatures
  disponibles de la catégorie et lui demander laquelle colle le mieux à l'opération.

## Notes / arbitrages pour l'oral

- Le **cœur déterministe** + une **relecture IA à la demande** = bon compromis fiabilité / coût /
  démonstration. Le tout-agent permanent (BannerAgency, MIMO) est plus puissant mais plus lourd,
  coûteux et aléatoire : à éviter pour une v1.
- Notre comparaison A / B / C reproduit le grand débat du domaine (sortie structurée vs génération
  libre) ; on conclut comme l'état de l'art, avec une implémentation réelle à l'appui.
