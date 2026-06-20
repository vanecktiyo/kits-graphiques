"""
ÉTAPE 4 - Interface web (FastAPI + Tailwind).

Parcours : le marketing saisit un brief créatif (1.1 mécanique, 1.2 message,
1.3 illustrations) et choisit les éléments à générer (2.1 site, 2.2 publicité)
-> Claude rédige le copy (generer_copy) -> on génère le kit (generer_kit)
-> aperçu, ajustement/régénération, puis téléchargement du kit en .zip.

Lancer (depuis la racine du projet) :
  .venv/Scripts/python.exe -m uvicorn api:app --app-dir backend --reload
Puis ouvrir : http://127.0.0.1:8000

Note : les routes sont des fonctions "def" (non "async"). FastAPI les exécute
dans un thread séparé, ce qui permet d'utiliser Playwright en mode synchrone.
"""

import io
import sys
import time
import zipfile
from pathlib import Path

# backend/ doit être sur le chemin pour importer les modules voisins (generer_copy...).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from generer_copy import generer_copy
from generer_kit import FORMATS, SORTIE, generer_kit, themes_transverses

RACINE = Path(__file__).resolve().parent.parent   # racine du projet

app = FastAPI(title="Gefradis - Generateur de bannieres")
templates = Jinja2Templates(directory=str(RACINE / "frontend" / "templates"))
app.mount("/output", StaticFiles(directory=str(RACINE / "output")), name="output")
app.mount("/static", StaticFiles(directory=str(RACINE / "frontend" / "static")), name="static")
app.mount("/assets", StaticFiles(directory=str(RACINE / "assets")), name="assets")   # logo, etc.


def _filtre(prefixe):
    return [f for f in FORMATS if f[0].startswith(prefixe)]


# Les éléments à générer, regroupés comme dans le cahier des charges (2.1 / 2.2).
ELEMENTS = [
    {"titre": "2.1 · Site", "groupes": [
        ("", _filtre("site_")),
    ]},
    {"titre": "2.2 · Acquisition publicitaire", "groupes": [
        ("Google Display", _filtre("display_")),
        ("Google Pmax", _filtre("pmax_")),
        ("Meta", _filtre("meta_")),
    ]},
]


def _formats_choisis(noms):
    """Filtre la liste FORMATS selon les cases cochées (toutes si rien de coché)."""
    choisis = [f for f in FORMATS if f[0] in noms]
    return choisis or FORMATS


def _resultat(request, brief, copy, formats_choisis, display_versions=("statique", "anime")):
    """Construit la page de résultat (copy éditable + aperçus).

    Pour un format Display, on affiche séparément la version statique (PNG) et la
    version animée (GIF), selon les versions demandées."""
    images = []
    for nom, l, h in formats_choisis:
        if nom.startswith("display_"):
            if "statique" in display_versions:
                images.append({"nom": nom, "largeur": l, "hauteur": h,
                               "fichier": f"{nom}.png", "variante": "statique"})
            if "anime" in display_versions:
                images.append({"nom": nom, "largeur": l, "hauteur": h,
                               "fichier": f"{nom}.gif", "variante": "animé"})
        else:
            images.append({"nom": nom, "largeur": l, "hauteur": h,
                           "fichier": f"{nom}.png", "variante": None})
    return templates.TemplateResponse(
        request=request,
        name="interface.html",
        context={
            "elements": ELEMENTS,
            "brief": brief,
            "copy": copy,
            "images": images,
            "noms_choisis": [f[0] for f in formats_choisis],
            "display_versions": list(display_versions),
            "cache": int(time.time()),   # anti-cache pour rafraîchir les images
        },
    )


@app.get("/", response_class=HTMLResponse)
def accueil(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="interface.html",
        context={"elements": ELEMENTS},
    )


@app.post("/generer", response_class=HTMLResponse)
def generer(
    request: Request,
    mecanique: str = Form(""),
    message: str = Form(...),
    illustrations: str = Form(""),
    illustrer: str = Form("1"),             # "1" = ajouter une image produit (choix du formulaire)
    cta: str = Form(""),                    # texte du bouton (vide = pas de bouton) ; choix du formulaire
    couleur_fond: str = Form("#253081"),    # fond choisi dans le formulaire
    formats: list[str] = Form(default=[]),
    display_versions: list[str] = Form(default=["statique", "anime"]),  # display : statique / animé
):
    brief = {"mecanique": mecanique, "message": message, "illustrations": illustrations}
    copy = generer_copy(brief, themes=themes_transverses())   # texte + choix du thème
    copy["couleur_fond"] = couleur_fond     # le fond ne vient pas de Claude
    copy["illustrer"] = bool(illustrer)     # l'image vient du formulaire, plus de Claude
    copy["cta"] = cta                       # le bouton vient du formulaire, plus de Claude
    choisis = _formats_choisis(formats)
    generer_kit(copy, formats=choisis,
                display_statique="statique" in display_versions,
                display_anime="anime" in display_versions)
    return _resultat(request, brief, copy, choisis, display_versions)


@app.post("/ajuster", response_class=HTMLResponse)
def ajuster(
    request: Request,
    mecanique: str = Form(""),
    message: str = Form(""),
    illustrations: str = Form(""),
    categorie: str = Form("transversale"),   # catégorie déduite, transmise du résultat
    couleur_fond: str = Form("#253081"),     # couleur de fond, transmise du résultat
    illustrer: str = Form(""),               # "1" si une image est voulue (transmis)
    offre_type: str = Form("montant"),       # montant / pourcentage / texte (transmis)
    theme_transverse: str = Form(""),        # thème transverse choisi par Claude (transmis)
    date_validite: str = Form(""),           # date de validité (éditable)
    palier_condition: list[str] = Form(default=[]),  # paliers : seuils (éditables)
    palier_valeur: list[str] = Form(default=[]),     # paliers : valeurs (éditables)
    titre: str = Form(...),
    offre_label: str = Form(""),
    offre_nombre: str = Form(""),
    offre_suffixe: str = Form(""),
    offre_texte: str = Form(""),
    cta: str = Form(""),
    formats: list[str] = Form(default=[]),
    display_versions: list[str] = Form(default=["statique", "anime"]),
):
    # On ne rappelle PAS Claude : on re-rend à partir du texte modifié à la main.
    paliers = [{"condition": c.strip(), "valeur": v.strip()}
               for c, v in zip(palier_condition, palier_valeur)
               if c.strip() and v.strip()]
    copy = {"categorie": categorie, "titre": titre, "offre_type": offre_type,
            "offre_label": offre_label, "offre_nombre": offre_nombre,
            "offre_suffixe": offre_suffixe, "offre_texte": offre_texte,
            "cta": cta, "couleur_fond": couleur_fond, "illustrer": bool(illustrer),
            "theme_transverse": theme_transverse,
            "paliers": paliers, "date_validite": date_validite}
    brief = {"mecanique": mecanique, "message": message, "illustrations": illustrations}
    choisis = _formats_choisis(formats)
    generer_kit(copy, formats=choisis,
                display_statique="statique" in display_versions,
                display_anime="anime" in display_versions)
    return _resultat(request, brief, copy, choisis, display_versions)


@app.get("/telecharger")
def telecharger():
    """Zippe le contenu de output/kit et le renvoie en téléchargement."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(list(SORTIE.glob("*.png")) + list(SORTIE.glob("*.gif"))):
            zf.write(f, arcname=f.name)
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=kit_gefradis.zip"},
    )


if __name__ == "__main__":
    # Permet de lancer aussi avec :  python backend/api.py
    # (l'équivalent du app.run() de Flask). Pour le rechargement auto en dev,
    # préférer : uvicorn api:app --app-dir backend --reload
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
