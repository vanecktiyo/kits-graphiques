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
from generer_kit import FORMATS, SORTIE, generer_kit

RACINE = Path(__file__).resolve().parent.parent   # racine du projet

app = FastAPI(title="Gefradis - Generateur de bannieres")
templates = Jinja2Templates(directory=str(RACINE / "frontend" / "templates"))
app.mount("/output", StaticFiles(directory=str(RACINE / "output")), name="output")
app.mount("/static", StaticFiles(directory=str(RACINE / "frontend" / "static")), name="static")


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


def _resultat(request, brief, copy, formats_choisis):
    """Construit la page de résultat (copy éditable + aperçus)."""
    images = [
        {"nom": nom, "largeur": l, "hauteur": h, "fichier": f"{nom}.png"}
        for nom, l, h in formats_choisis
    ]
    return templates.TemplateResponse(
        request=request,
        name="interface.html",
        context={
            "elements": ELEMENTS,
            "brief": brief,
            "copy": copy,
            "images": images,
            "noms_choisis": [f[0] for f in formats_choisis],
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
    formats: list[str] = Form(default=[]),
):
    brief = {"mecanique": mecanique, "message": message, "illustrations": illustrations}
    copy = generer_copy(brief)              # Claude rédige le texte (JSON)
    choisis = _formats_choisis(formats)
    generer_kit(copy, formats=choisis)      # Playwright rend les PNG
    return _resultat(request, brief, copy, choisis)


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
    titre: str = Form(...),
    offre_label: str = Form(""),
    offre_nombre: str = Form(""),
    offre_suffixe: str = Form(""),
    offre_texte: str = Form(""),
    cta: str = Form(""),
    formats: list[str] = Form(default=[]),
):
    # On ne rappelle PAS Claude : on re-rend à partir du texte modifié à la main.
    copy = {"categorie": categorie, "titre": titre, "offre_type": offre_type,
            "offre_label": offre_label, "offre_nombre": offre_nombre,
            "offre_suffixe": offre_suffixe, "offre_texte": offre_texte,
            "cta": cta, "couleur_fond": couleur_fond, "illustrer": bool(illustrer)}
    brief = {"mecanique": mecanique, "message": message, "illustrations": illustrations}
    choisis = _formats_choisis(formats)
    generer_kit(copy, formats=choisis)
    return _resultat(request, brief, copy, choisis)


@app.get("/telecharger")
def telecharger():
    """Zippe le contenu de output/kit et le renvoie en téléchargement."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for png in sorted(SORTIE.glob("*.png")):
            zf.write(png, arcname=png.name)
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
