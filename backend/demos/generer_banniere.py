"""
ÉTAPE 1 (suite) - Génération paramétrée.

Le même gabarit (banniere.html.j2) produit des bannières différentes selon le
"brief" qu'on lui donne. C'est ce qui rend l'outil générique : demain, c'est
Claude qui fournira ce brief (le texte) à partir de la saisie de l'utilisateur.

Lancer :  .venv/Scripts/python.exe app/generer_banniere.py
"""

import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")   # accents corrects à la console (Windows)

RACINE = Path(__file__).resolve().parent.parent
TEMPLATES = RACINE / "app" / "templates"
SORTIE = RACINE / "output"
SORTIE.mkdir(exist_ok=True)

env = Environment(loader=FileSystemLoader(str(TEMPLATES)))

# Dimensions du format (un bandeau catégorie desktop, pour l'exemple).
LARGEUR, HAUTEUR = 1200, 360

# --- Deux briefs DIFFÉRENTS : le même gabarit doit s'adapter à chacun. ---
BRIEFS = [
    (
        "banniere_reference.png",
        {
            "titre": "Les portes sur-mesure",
            "offre_label": "à partir de",
            "offre_nombre": "639",
            "offre_suffixe": ",85€",
        },
    ),
    (
        "banniere_gros_projets.png",
        {
            "titre": "Gros projets = Grosses Remises",
            "offre_label": "Jusqu'à",
            "offre_nombre": "500",
            "offre_suffixe": "€",
        },
    ),
]

gabarit = env.get_template("banniere.html.j2")
tmp = TEMPLATES / "_rendu_tmp.html"

with sync_playwright() as p:
    navigateur = p.chromium.launch()
    for nom_fichier, brief in BRIEFS:
        # 1) On remplit le gabarit avec le brief -> du HTML.
        html = gabarit.render(**brief)
        tmp.write_text(html, encoding="utf-8")
        # 2) On rend ce HTML en PNG, aux dimensions exactes.
        page = navigateur.new_page(
            viewport={"width": LARGEUR, "height": HAUTEUR},
            device_scale_factor=1,
        )
        page.goto(tmp.as_uri())
        page.evaluate("document.fonts.ready")
        page.locator(".banniere").screenshot(path=str(SORTIE / nom_fichier))
        page.close()
        print("Bannière générée :", SORTIE / nom_fichier)
    navigateur.close()

tmp.unlink(missing_ok=True)   # on retire le fichier HTML temporaire
