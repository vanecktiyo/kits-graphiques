"""
VERSION B (composable) — application web, copie fonctionnelle de la version A.

Mêmes parcours et options que A (brief 1.1/1.2/1.3, choix du fond, sélection des
formats 2.1/2.2, version Display statique/animée, panneau d'ajustement sans rappeler
Claude, téléchargement .zip). SEULE DIFFÉRENCE : le montage des bannières (gabarit
unique adaptatif via generer_kit) : la disposition est calculée par format par le code.
Indépendante de A : port 8001.

Lancer :  python composable/backend/api.py   (http://127.0.0.1:8001)
"""

import io
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from generer_copy import composer
from generer_kit import FORMATS, SORTIE, generer_kit, themes_transverses

RACINE = Path(__file__).resolve().parent.parent       # composable/

app = FastAPI(title="Gefradis - Generateur de bannieres (Version B)")
templates = Jinja2Templates(directory=str(RACINE / "frontend" / "templates"))
app.mount("/output", StaticFiles(directory=str(RACINE / "output")), name="output")
app.mount("/assets", StaticFiles(directory=str(RACINE / "assets")), name="assets")


def _filtre(prefixe):
    return [f for f in FORMATS if f[0].startswith(prefixe)]


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
    choisis = [f for f in FORMATS if f[0] in noms]
    return choisis or FORMATS


def _resultat(request, brief, copy, formats_choisis, display_versions=("statique", "anime")):
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
            "cache": int(time.time()),
        },
    )


def _rendre_erreur(request, brief, noms_formats, display_versions, exc):
    """Réaffiche le formulaire avec un message d'erreur clair (pas de page d'erreur brute)."""
    code = getattr(exc, "status_code", None)
    texte = str(exc).lower()
    if code in (429, 529) or "overloaded" in texte or "rate limit" in texte:
        msg = ("Le service de génération est momentanément très sollicité. "
               "Réessayez dans quelques instants.")
    else:
        msg = "Une erreur est survenue pendant la génération. Merci de réessayer."
    return templates.TemplateResponse(
        request=request, name="interface.html",
        context={"elements": ELEMENTS, "brief": brief, "erreur": msg,
                 "noms_choisis": noms_formats, "display_versions": display_versions},
    )


@app.get("/", response_class=HTMLResponse)
def accueil(request: Request):
    return templates.TemplateResponse(
        request=request, name="interface.html",
        context={"elements": ELEMENTS},
    )


@app.post("/generer", response_class=HTMLResponse)
def generer(
    request: Request,
    mecanique: str = Form(""),
    message: str = Form(...),
    illustrations: str = Form(""),
    illustrer: str = Form(""),              # défaut SÛR : pas d'image si l'info n'est pas envoyée
    cta: str = Form(""),                    # texte du bouton (vide = pas de bouton) ; formulaire
    couleur_fond: str = Form("#253081"),
    formats: list[str] = Form(default=[]),
    display_versions: list[str] = Form(default=["statique", "anime"]),
):
    brief = {"mecanique": mecanique, "message": message, "illustrations": illustrations}
    try:
        copy = composer(brief, themes=themes_transverses())   # texte (éditorial)
        copy["couleur_fond"] = couleur_fond                    # le fond vient du formulaire
        copy["illustrer"] = illustrer.strip().lower() in ("1", "true", "on", "oui")  # image : formulaire
        copy["cta"] = cta                                      # le bouton vient du formulaire
        choisis = _formats_choisis(formats)
        generer_kit(copy, formats=choisis,
                    display_statique="statique" in display_versions,
                    display_anime="anime" in display_versions)
    except Exception as exc:
        return _rendre_erreur(request, brief, formats, display_versions, exc)
    return _resultat(request, brief, copy, choisis, display_versions)


@app.post("/ajuster", response_class=HTMLResponse)
def ajuster(
    request: Request,
    mecanique: str = Form(""),
    message: str = Form(""),
    illustrations: str = Form(""),
    categorie: str = Form("transversale"),
    couleur_fond: str = Form("#253081"),
    illustrer: str = Form(""),
    offre_type: str = Form("montant"),
    theme_transverse: str = Form(""),
    date_validite: str = Form(""),
    palier_condition: list[str] = Form(default=[]),
    palier_valeur: list[str] = Form(default=[]),
    titre: str = Form(...),
    sous_titre: str = Form(""),
    offre_label: str = Form(""),
    offre_nombre: str = Form(""),
    offre_suffixe: str = Form(""),
    offre_texte: str = Form(""),
    cta: str = Form(""),
    formats: list[str] = Form(default=[]),
    display_versions: list[str] = Form(default=["statique", "anime"]),
):
    # On ne rappelle PAS Claude : on re-rend à partir du copy modifié à la main.
    brief = {"mecanique": mecanique, "message": message, "illustrations": illustrations}
    try:
        paliers = [{"condition": c.strip(), "valeur": v.strip()}
                   for c, v in zip(palier_condition, palier_valeur)
                   if c.strip() and v.strip()]
        copy = {"categorie": categorie, "titre": titre, "sous_titre": sous_titre,
                "offre_type": offre_type, "offre_label": offre_label,
                "offre_nombre": offre_nombre, "offre_suffixe": offre_suffixe,
                "offre_texte": offre_texte, "cta": cta, "couleur_fond": couleur_fond,
                "illustrer": illustrer.strip().lower() in ("1", "true", "on", "oui"),
                "theme_transverse": theme_transverse, "paliers": paliers,
                "date_validite": date_validite}
        choisis = _formats_choisis(formats)
        generer_kit(copy, formats=choisis,
                    display_statique="statique" in display_versions,
                    display_anime="anime" in display_versions)
    except Exception as exc:
        return _rendre_erreur(request, brief, formats, display_versions, exc)
    return _resultat(request, brief, copy, choisis, display_versions)


@app.get("/telecharger")
def telecharger():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(list(SORTIE.glob("*.png")) + list(SORTIE.glob("*.gif"))):
            zf.write(f, arcname=f.name)
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=kit_gefradis_B.zip"},
    )


if __name__ == "__main__":
    import os
    import uvicorn
    # En local : 127.0.0.1:8001. En conteneur/Cloud Run : HOST=0.0.0.0 et PORT injectés.
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"),
                port=int(os.environ.get("PORT", "8001")))
