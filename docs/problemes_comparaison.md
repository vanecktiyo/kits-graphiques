# Journal des problèmes à résoudre (comparaison A vs B)

But : pendant les tests des briefs (M1, M2, M4, P1, A2…), on consigne ici les défauts
de chaque version. À la fin, on choisit la version finale et on corrige sa liste.

Rappel : la version C (libre / full-LLM) est écartée (résultats imprévisibles, lente
et coûteuse). La comparaison se joue entre A (gabarits figés) et B (gabarit composable).

Légende statut : ⬜ à résoudre · ✅ résolu

---

## Corrections appliquées (19 juin 2026) — à re-tester sur les deux versions

**Version A**
- ✅ Rendu **2x** (net, plus de flou) — `device_scale_factor=2`.
- ✅ **Logo ne chevauche plus le titre** (pub illustrée) : logo toujours dans le flux.
- ✅ **Prix moins géant** (gabarit colonne : nombre ×2,3 → ×1,7).
- ✅ **Suffixe court** + **titre = accroche** (jamais l'offre) via le prompt.

**Version B**
- ✅ **Image affichée AVEC les paliers** (empilé sur carré/portrait, côte à côte sur paysage) ;
  l'indice « centre » ne supprime plus l'image.
- ✅ **Tout le cadre est mis à l'échelle** : plus de bouton coupé, plus de débordement
  d'en-tête (mobile OK), tout tient dans chaque format.
- ✅ **Échelle des en-têtes** revue (base sur la hauteur).
- ✅ **Suffixe court** + **titre = accroche** + tailles d'offre en côte à côte réduites.

Vérifié sur M4 (image + paliers) et P3 (suffixe long « -25% sur la motorisation » → « % »).

**Re-test M1 (relancé)** : OK des deux côtés. A net + équilibré ; B en-tête mobile ne déborde
plus, prix sur une ligne. Affinage B : image **à côté** du texte dès le carré (cote) sans
paliers, empilé seulement en portrait. Reliquat mineur B : « À partir de » sur deux lignes en
côte à côte sur le carré (colonne texte étroite).

Reste à refaire la passe complète des autres briefs sur A et B.

---

## Version B (composable) — problèmes à résoudre

### M1 (Portes, image + bouton, fond bleu)
- ⬜ **En-tête mobile `site_header_hp_mobile` (426x575) : débordement majeur.** Titre
  coupé des deux côtés, « À partir de » cassé en trois lignes, bloc prix « 639,85€ »
  qui sort du cadre. Cause : l'en-tête réutilise l'échelle des grands formats carrés
  (titre et prix trop gros) ; l'ajustement auto ne réduit que le titre, pas le prix.
- ⬜ **En-tête desktop `site_header_hp_desktop` (1900x456) : trop petit / trop de vide.**
  Titre et image produit plus petits que chez A, mauvaise occupation de l'espace.
- ⬜ **Côte à côte (carré 1080, box 300x250) : prix surdimensionné** → le libellé
  « À partir de » passe à la ligne (3 lignes verticales). À réduire + empêcher le retour
  à la ligne du libellé.
- ⬜ **Échelle générale plus prudente que A** : titre et images produit plus petits, moins
  d'impact sur les formats illustrés.
- ⬜ **Logo un peu gros / centré** sur les petits formats.

### M2 (Black Friday, transverse + paliers, fond foncé)
- ⬜ **Le visuel d'événement / l'image produit n'apparaît PAS dans les pubs** (carré 1080,
  box 300x250, paysage…). Seul le bandeau affiche le visuel BLACK FRIDAY. **C'est le défaut
  principal pointé : B ne gère pas le cas « image + paliers » ni « image + disposition
  centrée ».** Cause : la règle « paliers → disposition centrée sans image » et l'indice
  « centre » proposé par Claude suppriment l'image. Correctif prévu : afficher l'image
  (côte à côte / empilé) dès que `illustrer` est vrai, avec les paliers placés dans le
  bloc texte À CÔTÉ de l'image (comme A), au lieu de les opposer.

### M3 (Fenêtres, sans image, typographique, fond clair)
- ⬜ **Titre redondant avec l'offre.** Claude (composer de B) a mis « 100 € offerts par
  fenêtre » à la fois comme accroche ET comme offre dans le bloc jaune. A obtient une vraie
  accroche distincte (« Rénovez vos fenêtres, isolez mieux ») + l'offre. Correctif prévu :
  renforcer le prompt du composer pour que le titre soit une accroche, jamais la répétition
  de l'offre.
- Bon point : le prix est mieux équilibré que chez A (taille homogène, pas de nombre géant).

### M4 (paliers + date + image + bouton, fond bleu)
- ⬜ **Confirme le défaut M2 : image produit absente dans toutes les pubs** (carré, portrait,
  paysage) alors que le brief demande « une image de nos produits ». Seul le bandeau montre
  les produits. Même cause (paliers → centré sans image).
- Bons points : copy plus inspirée que A (« Plus votre projet grandit, plus vous économisez »)
  et paliers plus aérés / équilibrés. Visuellement très propre, hors absence d'image.

### P1 (Fenêtres, pourcentage + pastille de coin + image, fond clair)
- ✅ **Bien géré.** Pastille « -30% » dans le coin + image fenêtres corrects sur tous les
  formats (carré, portrait, box, bandeau). Sans paliers, l'image s'affiche bien : ça isole
  le bug d'image au seul cas « image + paliers ».
- Notes mineures : copy un peu raccourcie (« Déstockage fenêtres PVC » sans « fin de série »),
  logo encore un peu gros (déjà noté).

### P2 (French Days, transverse thème inconnu, -20%, image, fond bleu)
- ⬜ **Image absente alors qu'il n'y a PAS de paliers.** Cause : Claude a proposé la
  disposition « centre », et ma règle laisse « centre » supprimer l'image. Donc le bug
  d'image de B vient aussi de l'indice « centre », pas seulement des paliers. Correctif :
  afficher l'image dès que `illustrer` est vrai, quel que soit l'indice de disposition.
- ⬜ **Offre dans le titre** : « French Days : -20% sur tout » répète le « -20% » présent dans
  le bloc jaune. Même axe de correction que M3 (titre = accroche, pas l'offre).
- Bon point : repli sur la promo par défaut prévu (mais non affiché ici à cause du bug image).

### P3 (Volets roulants, -25% sur la motorisation, sans image, bouton, fond clair)
- ⬜ **Suffixe long mal géré** (« % sur la motorisation » coincé dans le bloc, « -25 » encore
  gros), mais nettement mieux tenu que A. Voir note partagée.
- Bons points : copy (« Volets roulants motorisés, confort malin ») et bouton (« Demander un
  devis gratuit ») meilleurs que A.

### A1 (Baies vitrées, avantage « Pose offerte », image + bouton, fond clair)
- ✅ **Bien géré.** Bloc jaune « Pose offerte », **image baie affichée** (Claude a choisi
  « côte à côte », donc pas de bug d'image), bouton « Prendre rendez-vous ». Rendu net (2x).
- Petit doublon partagé : le titre reprend « pose offerte » déjà dans le bloc (voir note).

### A2 (avantage « Livraison offerte », sans image, fond foncé, transverse)
- ✅ Typographique propre, logo bleu-jaune correct, bandeau OK, rendu net (2x).
- ⬜ **Doublon marqué (partagé)** : titre ≈ bloc jaune (« Livraison offerte dès 1000 € »).
  Voir note partagée sur le type avantage.

### A3 (Portails, avantage « Motorisation offerte », image + bouton, fond clair)
- ✅ **Bien géré.** Avantage dans le bloc, image portail affichée (Claude a choisi côte à
  côte), bouton présent, titre distinct, rendu net (2x).
- ⬜ Note mineure : le bloc « Motorisation offerte » passe à la ligne et est un peu gros sur
  le carré (taille du texte d'offre en côte à côte). Même axe que « prix gros en côte à côte ».

### Cas cahier des charges (Gros projets = Grosses Remises, paliers, transverse)
- ✅ **Très bien géré.** Les 2 paliers extraits et présentés proprement (carré, paysage,
  bandeau), avec gestion intelligente de l'ambiguïté du brief (« Sur les commandes plus
  importantes »). Fidèle à la mécanique en paliers, sans nombre géant. Meilleur que A sur
  LE cas de référence du sujet.
- ⬜ À vérifier : le bouton semble présent sur le format fin mais pas sur le carré chargé de
  paliers (peut-être poussé hors cadre). À corriger si confirmé (réserver la place du bouton).

---

## Version A (gabarits figés) — problèmes à résoudre

### Global (tous les briefs, tous les formats)
- ⬜ **Rendu en basse résolution (1x), images floues.** A capture en
  `device_scale_factor=1` : un 300x250 fait 300x250 px, un 1080 fait 1080 px. Net à 100 %,
  mais **flou dès qu'on agrandit** (galerie) ou **sur écran retina**. B rend en **2x**
  (600x500, 2160 px) donc net. Correctif : passer A en `device_scale_factor=2`. C'est le
  défaut le plus visible de A à l'œil, même s'il est trivial à corriger.

### M1 (Portes, image + bouton, fond bleu)
- (rien à signaler : rendus conformes et propres sur tous les formats observés)

### M2 (Black Friday, transverse + paliers, fond foncé)
- ⬜ **Carré `meta_1080x1080` : le logo chevauche le titre.** En disposition « row »
  (illustrée), le logo en position absolue (haut gauche) passe par-dessus le titre
  « Black Friday » qui démarre tout en haut. Correctif prévu : réserver l'espace du logo
  (padding haut) ou passer le logo dans le flux en mode row illustré.
- Bon point : le visuel BLACK FRIDAY apparaît bien dans toutes les pubs (paysage, box…)
  à côté des paliers / de l'offre.

### M3 (Fenêtres, sans image, typographique, fond clair)
- ⬜ **Prix trop gros sur les formats typographiques (sans image).** Le nombre
  (`.prix .nombre` = base × 2,3 dans le gabarit colonne) écrase le suffixe, surtout quand
  il est long (« € offerts par fenêtre »). Visuellement déséquilibré. Correctif prévu :
  réduire la taille du nombre et/ou mieux équilibrer nombre vs suffixe, surtout quand le
  suffixe est long.

### M4 (paliers + date + image + bouton, fond bleu)
- ⬜ **Confirme le défaut M2 : le logo chevauche le titre sur le carré `meta_1080x1080`**
  (« Gros » masqué). Le bug revient sur les formats carrés illustrés avec contenu qui
  démarre en haut. Même correctif que M2 (réserver l'espace du logo en mode row).
- Bons points : portrait 1080x1350 et paysage excellents (titre complet, date, 2 paliers,
  bouton ET image produit). A gère bien le cas « image + paliers » ensemble.

### P1 (Fenêtres, pourcentage + pastille de coin + image, fond clair)
- ✅ **Bien géré.** Pastille « -30% » dans le coin + image fenêtres corrects sur tous les
  formats (carré, portrait, box, bandeau). Copy complète (« ...fin de série »).

### P2 (French Days, transverse thème inconnu, -20%, image, fond bleu)
- ⬜ **Confirme « prix trop gros », version pourcentage.** Le « -20 » est surdimensionné et
  le « % » réduit en exposant minuscule → déséquilibré. La signature « gros nombre + petit
  suffixe » convient aux prix en €, pas aux pourcentages. Correctif : pour les pourcentages,
  équilibrer nombre et suffixe et réduire la taille globale.
- Bons points : repli sur la promo par défaut OK (image gamme affichée car le thème
  « French Days » n'existe pas), logo bleu-jaune correct sur fond foncé.

### P3 (Volets roulants, -25% sur la motorisation, sans image, bouton, fond clair)
- ⬜ **Catastrophique sur le carré.** Le « -25 » est énorme (gabarit colonne ×2,3) et
  « % sur la motorisation » déborde sur deux lignes. Cause double : suffixe trop long mis
  par Claude + signature gros-nombre inadaptée aux suffixes longs. Voir note partagée.

### A1 (Baies vitrées, avantage « Pose offerte », image + bouton, fond clair)
- ✅ **Bien géré.** Bloc jaune « Pose offerte » (texte, sans chiffre), image baie affichée,
  bouton « Je prends rendez-vous ». Type avantage correct.
- Petit doublon partagé : le titre reprend « pose offerte » déjà dans le bloc (voir note).

### A2 (avantage « Livraison offerte », sans image, fond foncé, transverse)
- ✅ Typographique propre, logo bleu-jaune correct sur fond foncé, bandeau OK.
- ⬜ **Doublon marqué (partagé) :** titre « Livraison offerte dès 1000 € » ≈ bloc « Livraison
  offerte dès 1000 € d'achat ». Voir note partagée sur le type avantage.

### A3 (Portails, avantage « Motorisation offerte », image + bouton, fond clair)
- ✅ **Bien géré.** Avantage dans le bloc, image portail affichée, bouton présent. Titre
  distinct de l'offre (pas de doublon ici). Bloc compact sur une ligne.

### Cas cahier des charges (Gros projets = Grosses Remises, paliers, transverse)
- ⬜ **A n'a montré que l'offre résumée « 500 € offerts »** (les paliers n'ont pas été gardés
  ce run), avec le **« 500 » géant** sur le carré (défaut de taille récurrent). Moins fidèle à
  la mécanique en paliers que B sur LE cas de référence du sujet.

---

## Notes transverses
- Le fond clair attendu pour M1 (#E7E9F4) n'a pas été sélectionné au test (fond bleu par
  défaut des deux côtés). Sans impact sur la comparaison (même fond pour A et B).
- Variation de texte entre A et B (« Jusqu'à la fin du mois » vs « fin du mois ») : c'est
  une variation de rédaction de Claude, pas un défaut de mise en page.
- **Ressenti visuel (avis utilisateur)** : B est souvent jugé plus agréable que A. Raisons :
  rendu net (2x), texte et logo plus présents (plus d'impact), paliers plus aérés, copy
  parfois plus inspirée. La note « logo un peu gros » de B est donc à relativiser (goût).
- **Pour la décision finale** : la plupart des défauts des deux versions sont corrigeables.
  A = très fiable mais rendu 1x flou (trivial à corriger) + chevauchement logo/titre + prix
  trop gros. B = plus beau rendu, mais montage image + paliers à finir + échelles d'en-tête.
- **PARTAGÉ (A et B) — suffixe d'offre trop long (P3).** Quand l'offre est « -25% sur la
  motorisation », Claude met « % sur la motorisation » dans `offre_suffixe`, ce qui coince
  une phrase longue dans le bloc jaune à côté d'un nombre géant. Correctif : le bloc jaune
  ne doit contenir que la valeur courte (« -25% ») ; le complément (« sur la motorisation »)
  va dans le libellé ou le titre. À régler dans le prompt (suffixe court) + équilibrage du
  bloc offre. Concerne les deux versions.
- **PARTAGÉ (A et B) — titre qui répète l'offre, surtout en type avantage (M3, A1, A2).**
  Claude met souvent l'offre à la fois en titre ET dans le bloc jaune (« Livraison offerte »
  des deux côtés). Correctif (prompt) : le titre doit être une accroche distincte (bénéfice,
  émotion), jamais la répétition littérale de l'offre. Concerne les deux versions.
