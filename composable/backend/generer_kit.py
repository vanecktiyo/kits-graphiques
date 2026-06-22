"""
VERSION B (composable) — assemblage du kit.

Même logique que la version A (mêmes images de catégorie / transverse, même logo
selon le fond, mêmes formats, même animation GIF des Display, couleur de fond choisie
dans le formulaire). SEULE DIFFÉRENCE : le MONTAGE. Au lieu d'un gabarit figé par type
de bannière, B rend un GABARIT UNIQUE et adaptatif (banniere_composable.html.j2) en lui
passant une DISPOSITION calculée pour chaque format (centre, côte à côte, empilé, ligne,
bandeau). La disposition est calculée par le code pour chaque format, selon le contenu
(image demandée, paliers) ; la charte reste figée dans le gabarit.

Indépendante de A : composants, assets et port (8001) distincts.
"""

import io
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

DOSSIER = Path(__file__).resolve().parent          # composable/backend
RACINE = DOSSIER.parent                              # composable/
TEMPLATES = DOSSIER / "bannieres"
SORTIE = RACINE / "output" / "kit"
SORTIE.mkdir(parents=True, exist_ok=True)

env = Environment(loader=FileSystemLoader(str(TEMPLATES)))

# Mêmes formats que la version A (pour comparer à brief identique).
FORMATS = [
    ("meta_1080x1080", 1080, 1080),
    ("meta_1080x1350", 1080, 1350),
    ("meta_1080x1920", 1080, 1920),
    ("display_300x250", 300, 250),
    ("display_160x600", 160, 600),
    ("display_728x90", 728, 90),
    ("display_320x50", 320, 50),
    ("pmax_paysage_1200x628", 1200, 628),
    ("pmax_carre_1200x1200", 1200, 1200),
    ("pmax_portrait_960x1200", 960, 1200),
    ("site_header_hp_desktop", 1900, 456),
    ("site_header_hp_mobile", 426, 575),
    ("site_bandeau_categorie", 2560, 280),
]

CHAMPS_GABARIT = ("titre", "sous_titre", "offre_label", "offre_nombre", "offre_suffixe")
FONDS_FONCES = {"#253081", "#040c4d"}

ASSETS_CAT = RACINE / "assets" / "produit" / "catégorie"
TRANSVERSE = RACINE / "assets" / "produit" / "transverses"
LOGOS = RACINE / "assets" / "logo"
LOGOS_CACHE = RACINE / "output" / "_logos"
_EXT_IMG = {".png", ".jpg", ".jpeg", ".webp"}


# ----------------------------------------------------------------------------
# Images (identique à la version A).
# ----------------------------------------------------------------------------
def _image_categorie(categorie: str, sous_dossier: str):
    dossier = ASSETS_CAT / categorie / sous_dossier
    if not dossier.is_dir():
        return None
    images = sorted(dossier.glob("*.webp"))
    return images[0].resolve().as_uri() if images else None


def themes_transverses():
    if not TRANSVERSE.is_dir():
        return []
    return sorted(d.name for d in TRANSVERSE.iterdir() if d.is_dir())


def _premiere_image(dossier: Path):
    if not dossier.is_dir():
        return None
    images = sorted(p for p in dossier.iterdir() if p.suffix.lower() in _EXT_IMG)
    return images[0].resolve().as_uri() if images else None


def _fichier_transverse(stem: str):
    if not TRANSVERSE.is_dir():
        return None
    for p in sorted(TRANSVERSE.iterdir()):
        if p.is_file() and p.stem.lower() == stem.lower() and p.suffix.lower() in _EXT_IMG:
            return p.resolve().as_uri()
    return None


def _image_theme_transverse(theme: str):
    return _premiere_image(TRANSVERSE / theme) if theme else None


_LOGO_VARIANTES = {
    "clair": ("gefradis-logo-bleu-blanc.png", "cle"),
    "fonce": ("gefradis-logo-bleu-jaune.png", "bord"),
}


def _logo_transparent(src_name: str, mode: str):
    dst = LOGOS_CACHE / src_name
    if dst.exists():
        return dst
    LOGOS_CACHE.mkdir(parents=True, exist_ok=True)
    if mode == "cle":
        im = Image.open(LOGOS / src_name).convert("RGBA")
        im.putdata([(r, g, b, 0) if r > 235 and g > 235 and b > 235 else (r, g, b, a)
                    for (r, g, b, a) in im.getdata()])
    else:  # "bord"
        im = Image.open(LOGOS / src_name).convert("RGB")
        w, h = im.size
        for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
            ImageDraw.floodfill(im, seed, (255, 0, 255), thresh=40)
        im = im.convert("RGBA")
        im.putdata([(r, g, b, 0) if (r, g, b) == (255, 0, 255) else (r, g, b, a)
                    for (r, g, b, a) in im.getdata()])
    im.save(dst)
    return dst


def _logo_uri(nom: str, fonce: bool):
    if nom.startswith("site_"):
        return None
    src, mode = _LOGO_VARIANTES["fonce" if fonce else "clair"]
    return _logo_transparent(src, mode).resolve().as_uri()


# ----------------------------------------------------------------------------
# Ajustement : mise à l'échelle des formats fins + réduction du titre si débordement.
# ----------------------------------------------------------------------------
_AJUSTER_ECHELLE = """() => {
  const b = document.querySelector('.banniere');
  const c = document.querySelector('.cadre');
  if (!b || !c) return;
  c.style.transform = 'none';
  // Mesure ROBUSTE du contenu : on prend l'enveloppe (rectangles réels) de tous les
  // éléments du cadre. Contrairement à scrollWidth/scrollHeight, ça capture un
  // débordement même quand le contenu est CENTRÉ et dépasse des deux côtés (paliers
  // trop larges, colonne de texte trop haute en côte à côte...).
  const br = b.getBoundingClientRect();
  const cr = c.getBoundingClientRect();
  let minL = Infinity, minT = Infinity, maxR = -Infinity, maxB = -Infinity;
  for (const el of c.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    minL = Math.min(minL, r.left); minT = Math.min(minT, r.top);
    maxR = Math.max(maxR, r.right); maxB = Math.max(maxB, r.bottom);
  }
  if (minL === Infinity) return;
  const marge = 0.98;                          // petite marge pour ne pas coller aux bords
  const sw = (br.width  * marge) / (maxR - minL);
  const sh = (br.height * marge) / (maxB - minT);
  let s = Math.min(sw, sh);
  if (c.classList.contains('ligne')) s = Math.min(s, 2.2);  // formats fins : agrandir pour remplir
  else s = Math.min(s, 1);                                  // formats normaux : seulement réduire
  // On réduit ET on RECENTRE le contenu dans la bannière : indispensable quand le
  // contenu n'est pas centré dans le cadre (empilé = contenu en haut), sinon réduire
  // depuis le centre du cadre le laisse décalé et il déborde encore.
  const ccx = (minL + maxR) / 2, ccy = (minT + maxB) / 2;
  const tx = (br.left + br.width / 2) - cr.left - (ccx - cr.left) * s;
  const ty = (br.top + br.height / 2) - cr.top - (ccy - cr.top) * s;
  c.style.transformOrigin = '0 0';
  c.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + s + ')';
}"""

# Animation GIF (identique au principe de A) : message -> + offre -> + bouton.
_SEL_OFFRE = ".offre, .offre-label, .prix, .paliers"
_SEL_CTA = ".cta"
_VISIBILITE = "([sel, v]) => document.querySelectorAll(sel).forEach(e => e.style.visibility = v)"


def _rendre_gif(page, chemin: str):
    cible = page.locator(".banniere")
    page.evaluate(_VISIBILITE, [_SEL_OFFRE, "hidden"])
    page.evaluate(_VISIBILITE, [_SEL_CTA, "hidden"])
    f1 = cible.screenshot()
    page.evaluate(_VISIBILITE, [_SEL_OFFRE, "visible"])
    f2 = cible.screenshot()
    page.evaluate(_VISIBILITE, [_SEL_CTA, "visible"])
    f3 = cible.screenshot()
    images = [Image.open(io.BytesIO(b)).convert("RGB") for b in (f1, f2, f3)]
    images[0].save(chemin, save_all=True, append_images=images[1:],
                   duration=[800, 900, 1600], loop=0, optimize=True)


# ----------------------------------------------------------------------------
# Disposition d'un format : c'est le « montage » propre à B. Le code adapte la
# disposition calculée pour chaque format ; la charte reste figée.
# ----------------------------------------------------------------------------
def _disposition_format(nom, largeur, hauteur, copy, image_promo):
    # Paliers : affichés partout sauf sur les bandes fines (disposition 'ligne',
    # hauteur < 120). Sur les formats étroits/portrait ils s'empilent en colonne,
    # sur les formats larges ils se mettent côte à côte ; le cadre met le tout à
    # l'échelle pour que rien ne déborde jamais.
    montrer_paliers = bool(copy.get("paliers")) and hauteur >= 200
    if nom.startswith("site_bandeau"):
        return "bandeau", montrer_paliers
    if nom.startswith("site_header"):
        return "centre", montrer_paliers            # en-tête typographique (sans image produit)
    if hauteur < 120:
        return "ligne", False
    # Pub : si une image est demandée, on l'affiche TOUJOURS ; les paliers vont à côté,
    # dans le bloc texte. Côte à côte si le format est large, empilé sinon (l'image dessous
    # laisse aux paliers toute la largeur). Sans image : composition centrée.
    if image_promo:
        # Paliers : besoin de largeur -> on empile plus tôt (image dessous). Sans paliers :
        # côte à côte dès le carré (plus équilibré), empilé sinon (portrait, formats étroits).
        seuil = 1.3 if montrer_paliers else 0.9
        return ("cote" if (largeur / hauteur) >= seuil else "empile"), montrer_paliers
    return "centre", montrer_paliers


def _base_format(nom, largeur, hauteur, disposition):
    if disposition == "bandeau":
        return round(hauteur * 0.14, 2)
    if nom == "site_header_hp_mobile":
        return round(min(largeur, hauteur) * 0.11, 2)    # mobile : accroche un peu plus petite
    if nom.startswith("site_header"):
        return round(min(largeur, hauteur) * 0.16, 2)   # base sur la plus petite dimension
    if disposition == "ligne":
        return round(hauteur * 0.5, 2)
    if disposition in ("cote", "empile"):
        return round(min(largeur, hauteur) * 0.095, 2)
    return round(min(largeur, hauteur) * 0.085, 2)


def generer_kit(copy: dict, formats=FORMATS, display_statique=True, display_anime=True):
    """Rend tous les formats du kit à partir d'un copy structuré (dict)."""
    for ancien in list(SORTIE.glob("*.png")) + list(SORTIE.glob("*.gif")):
        ancien.unlink()

    fond = copy.get("couleur_fond") or "#253081"
    fonce = fond.lower() in FONDS_FONCES
    contexte = {
        **{champ: copy.get(champ, "") for champ in CHAMPS_GABARIT},
        "offre_type": copy.get("offre_type", "montant"),
        "offre_texte": copy.get("offre_texte", ""),
        "paliers": copy.get("paliers", []),
        "date_validite": copy.get("date_validite", ""),
        "cta": copy.get("cta", ""),
        "couleur_fond": fond,
        "couleur_texte": "#ffffff" if fonce else "#040c4d",
        "couleur_bouton": "#ffffff" if fonce else "#253081",
        "couleur_bouton_texte": "#253081" if fonce else "#ffffff",
    }

    categorie = copy.get("categorie", "transversale")
    if copy.get("illustrer"):
        if categorie == "transversale":
            image_promo = (_image_theme_transverse(copy.get("theme_transverse", ""))
                           or _fichier_transverse("promo par défaut"))
        else:
            image_promo = _image_categorie(categorie, "promo")
    else:
        image_promo = None

    gabarit = env.get_template("banniere_composable.html.j2")
    tmp = TEMPLATES / "_rendu_tmp.html"

    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        for nom, largeur, hauteur in formats:
            disposition, montrer_paliers = _disposition_format(nom, largeur, hauteur, copy, image_promo)
            base = _base_format(nom, largeur, hauteur, disposition)
            logo = _logo_uri(nom, fonce)

            fond_image = evenement = image_uri = None
            if disposition == "bandeau":
                if categorie == "transversale":
                    fond_image = _fichier_transverse("bandeau")
                    evenement = _image_theme_transverse(copy.get("theme_transverse", ""))
                else:
                    fond_image = _image_categorie(categorie, "Bandeau page catégorie")
            elif disposition in ("cote", "empile", "hero"):
                image_uri = image_promo

            html = gabarit.render(
                largeur=largeur, hauteur=hauteur, base=base, disposition=disposition,
                logo_uri=logo, image_uri=image_uri, fond_image=fond_image,
                evenement_uri=evenement, montrer_paliers=montrer_paliers, **contexte,
            )
            tmp.write_text(html, encoding="utf-8")

            page = navigateur.new_page(viewport={"width": largeur, "height": hauteur},
                                       device_scale_factor=2)
            page.goto(tmp.as_uri())
            page.evaluate("document.fonts.ready")
            page.evaluate(_AJUSTER_ECHELLE)
            est_display = nom.startswith("display_")
            if not est_display or display_statique:
                page.locator(".banniere").screenshot(path=str(SORTIE / f"{nom}.png"))
            if est_display and display_anime:
                _rendre_gif(page, str(SORTIE / f"{nom}.gif"))
            page.close()
            print(f"Généré : {nom}  ({largeur}x{hauteur})")
        navigateur.close()

    tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    from generer_copy import composer
    BRIEF = {
        "mecanique": "100 € offerts dès 1000 € HT, 350 € dès 3000 €. Tout le catalogue. "
                     "Valable jusqu'au 30 juin 2026.",
        "message": "Opération « Gros projets = Grosses remises ».",
        "illustrations": "une image de nos produits, un bouton « J'en profite »",
    }
    copy = composer(BRIEF)
    copy["couleur_fond"] = "#253081"
    print("Copy composé :", copy)
    generer_kit(copy)
    print("Kit dans :", SORTIE)
