# État de l'art — génération de bannières publicitaires par IA

But : situer notre projet (un brief → contenu structuré → rendu fidèle à une charte) par
rapport aux travaux de recherche et aux outils industriels existants, et vérifier qu'on
est sur la bonne voie.

Rappel de notre approche : **Claude génère un JSON structuré** (le copy + l'offre), le code
l'injecte dans des **gabarits HTML/CSS** (charte figée), et **Playwright** rend chaque format
en image. On a comparé trois architectures : A (gabarits figés + JSON), B (gabarit composable
+ JSON), C (full LLM : Claude génère le HTML/CSS).

---

## Articles et systèmes les plus proches de notre sujet

### 1. CreatiPoster (2025) — le plus proche de notre version B
- **Résumé** : un modèle multimodal produit une **spécification JSON de chaque calque** (mise
  en page, hiérarchie, contenu, style), puis un modèle génère le fond. Éditable, multilingue,
  redimensionnable.
- **Stack** : « protocol model » multimodal → JSON multi-calques + modèle de fond conditionnel
  + rendu depuis le JSON. Jeu de données de 100 000 designs.
- **Année** : 2025
- **Lien** : https://arxiv.org/abs/2506.10890
- **Pertinence** : exactement notre principe (l'IA sort un **JSON structuré, pas des pixels**,
  et un moteur fait le rendu). Valide notre choix Claude → JSON → gabarit.

### 2. BannerAgency (2025, EMNLP) — notre cas d'usage exact
- **Résumé** : framework **sans entraînement** d'agents MLLM qui simulent une équipe de design
  (comprend la marque + le logo, génère un fond, un blueprint) et sort des **composants
  éditables (Figma/SVG)**, pas des pixels figés.
- **Stack** : MLLM de pointe en agents, génération d'image de fond, rendu SVG/Figma. Benchmark
  BannerRequest400 (100 logos, 400 requêtes).
- **Année** : 2025
- **Lien** : https://arxiv.org/abs/2503.11060
- **Pertinence** : même objectif que nous (bannières on-brand depuis un brief + logo) et même
  philosophie « sortie structurée éditable ». Eux multi-agents ; nous JSON + gabarits figés
  (plus déterministe).

### 3. LayoutGPT (2023) — LLM comme planificateur de mise en page
- **Résumé** : un LLM génère des **mises en page sous forme de feuilles de style (type CSS)**
  via des exemples en contexte. +20 à 40 % vs text-to-image, proche du niveau humain pour le
  layout.
- **Stack** : LLM (GPT) → représentation structurée de layout.
- **Année** : 2023
- **Lien** : https://arxiv.org/abs/2305.15393
- **Pertinence** : même idée que nous, l'IA produit une **représentation structurée** de la
  mise en page, pas l'image finale.

### 4. Design2Code (2024) — correspond à notre version C
- **Résumé** : 1er benchmark « design → code ». Des MLLM (GPT-4o/4V, Gemini, **Claude**)
  génèrent le **HTML/CSS** d'une page à partir d'une capture. Constat clé : les modèles
  **peinent à restituer les éléments visuels et à produire une mise en page correcte**.
- **Stack** : GPT-4o/4V, Gemini, Claude ; HTML/CSS ; 484 pages de test.
- **Année** : 2024
- **Lien** : https://arxiv.org/abs/2403.03163
- **Pertinence** : c'est **littéralement notre version C** (Claude génère le HTML/CSS). La
  recherche **confirme** que c'est peu fiable aujourd'hui. Ça valide notre décision d'écarter
  C et de garder le JSON structuré.

### 5. MIMO « Mirror in the Model » (2025)
- **Résumé** : agents multi-LLM/multimodaux **réflexifs** qui itèrent pour produire des
  bannières avec mise en page structurée, typo précise et **branding cohérent**, en
  détectant/corrigeant leurs erreurs.
- **Stack** : GPT-4o, agents hiérarchiques + boucle de raffinement.
- **Année** : 2025
- **Lien** : https://arxiv.org/abs/2507.03326
- **Pertinence** : confirme que **branding et typo cohérents = LE défi**. Eux le règlent par
  auto-correction ; nous par **charte figée dans le gabarit** (déterministe, sans aléa).

### 6. Vinci (2021, CHI) — pionnier du design d'affiches publicitaires
- **Résumé** : système intelligent qui génère des affiches publicitaires à partir d'un texte
  + une structure de calques hiérarchiques.
- **Année** : 2021
- **Lien** : https://dl.acm.org/doi/10.1145/3411764.3445117
- **Pertinence** : logique template/layout, proche de notre version A.

### 7. Luban d'Alibaba (~2018, industriel) — la preuve à l'échelle
- **Résumé** : outil de design IA qui génère **des dizaines de milliers de bannières par
  seconde** (Tmall), via **templates + apprentissage de la mise en page + rendu GPU**. Des
  centaines de millions de visuels produits.
- **Année** : ~2018
- **Lien** : https://www.alibabacloud.com/blog/alibaba-luban-ai-based-graphic-design-tool_594294
- **Pertinence** : preuve industrielle massive que l'approche « gabarit + données structurées
  + rendu » passe à l'échelle. C'est notre famille A/B.

### 8. Dynamic Creative Optimization (DCO) — le standard de la pub display
- **Résumé** : un **master template** avec des champs dynamiques (titre, image, prix, **CTA**)
  rempli par un **flux de données structuré** (JSON/XML). Le standard de la publicité
  programmatique.
- **Année** : standard industriel (années 2010 à aujourd'hui)
- **Lien** : https://en.wikipedia.org/wiki/Dynamic_creative_optimization
- **Pertinence** : c'est **exactement notre architecture** (gabarit + données structurées).
  Notre apport : c'est **l'IA qui génère le « flux »** (le copy) à partir d'un brief en langage
  naturel, au lieu d'un feed produit manuel.

---

## Synthèse : deux grandes familles, et où on se situe

| Famille | Principe | Travaux | Notre version |
|---|---|---|---|
| **A. LLM → représentation structurée → rendu déterministe** | l'IA sort du JSON / layout, un moteur rend (charte garantie) | CreatiPoster, LayoutGPT, DCO, Luban, Vinci, BannerAgency | **A et B** |
| **B. LLM → pixels / HTML direct** | l'IA produit l'image ou le code final | Design2Code (HTML), MIMO / diffusion (pixels) | **C** |

---

## Verdict : on est sur la bonne voie

- Notre approche (**Claude → JSON structuré → gabarits, charte figée**) est **la tendance
  dominante** en recherche récente (CreatiPoster, LayoutGPT, BannerAgency) **et** le standard
  industriel éprouvé (DCO, Luban).
- Notre **version C** (full LLM HTML) correspond à **Design2Code**, dont la conclusion est
  justement que c'est **peu fiable** aujourd'hui. Donc notre choix de l'écarter est **soutenu
  par la littérature**.
- Argument fort pour l'oral : notre comparaison **A / B / C reproduit, en petit, le grand débat
  du domaine** (sortie structurée vs génération libre), et on aboutit à la **même conclusion
  que l'état de l'art**, avec une implémentation réelle à l'appui.

---

## Différences honnêtes avec ces travaux (limites à assumer à l'oral)

- La plupart de ces travaux génèrent aussi le **fond / l'image** par IA (diffusion). Nous, on
  s'appuie sur une **banque d'assets fournie** (logo, photos produit) : plus sûr pour la charte,
  mais moins « créatif » sur le visuel. C'est un choix assumé (fiabilité > liberté).
- Les approches multi-agents (BannerAgency, MIMO) sont plus puissantes mais plus **lourdes et
  coûteuses** (plusieurs appels, boucles). Notre pipeline est **simple et déterministe**, adapté
  à un test technique et à une mise en production maîtrisée.

---

Sources : [BannerAgency](https://arxiv.org/abs/2503.11060) · [MIMO](https://arxiv.org/abs/2507.03326)
· [CreatiPoster](https://arxiv.org/abs/2506.10890) · [Design2Code](https://arxiv.org/abs/2403.03163)
· [LayoutGPT](https://arxiv.org/abs/2305.15393) · [Vinci](https://dl.acm.org/doi/10.1145/3411764.3445117)
· [Luban](https://www.alibabacloud.com/blog/alibaba-luban-ai-based-graphic-design-tool_594294)
· [DCO](https://en.wikipedia.org/wiki/Dynamic_creative_optimization)
