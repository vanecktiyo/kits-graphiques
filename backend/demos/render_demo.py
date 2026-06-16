"""
ÉTAPE 1 - Rendu d'une première bannière à la charte Gefradis.

Principe : on ouvre le gabarit HTML/CSS dans un navigateur sans interface
(Chromium, piloté par Playwright), à la taille exacte du format, puis on
prend une capture d'écran -> un fichier PNG.

Lancer :  .venv/Scripts/python.exe app/render_demo.py
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Sous Windows, la console est en cp1252 ; on force l'UTF-8 pour les accents.
sys.stdout.reconfigure(encoding="utf-8")

# Chemins du projet (calculés à partir de l'emplacement de ce fichier).
RACINE = Path(__file__).resolve().parent.parent
GABARIT = RACINE / "app" / "templates" / "banniere_demo.html"
SORTIE = RACINE / "output" / "banniere_demo_1200x360.png"

# Dimensions exactes du format visé (un bandeau catégorie desktop, pour l'exemple).
LARGEUR, HAUTEUR = 1200, 360

SORTIE.parent.mkdir(exist_ok=True)

with sync_playwright() as p:
    navigateur = p.chromium.launch()
    page = navigateur.new_page(
        viewport={"width": LARGEUR, "height": HAUTEUR},
        device_scale_factor=1,   # 1 = dimensions exactes (pas de retina)
    )
    # On ouvre le gabarit HTML local.
    page.goto(GABARIT.as_uri())
    # On attend que la police Cabin soit bien chargée avant la capture.
    page.evaluate("document.fonts.ready")
    # Capture de la bannière, aux dimensions exactes.
    page.locator(".banniere").screenshot(path=str(SORTIE))
    navigateur.close()

print(f"Bannière générée : {SORTIE}")
