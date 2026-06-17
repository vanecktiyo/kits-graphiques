"""
ÉTAPE 3 (branchement) - Du copy de Claude au KIT complet.

generer_copy.py (Claude) produit le texte structuré ; ce module l'injecte dans
les gabarits et rend chaque format en PNG (Playwright). Le copy n'est PLUS codé
en dur : il vient du brief saisi par le marketing.

Le gabarit s'adapte à la forme de chaque format grâce à une unité d'échelle
("base") calculée selon les dimensions : disposition EN LIGNE pour les formats
très courts (hauteur < 120), EN COLONNE sinon (centré, ou réparti si très vertical).

Lancer :  .venv/Scripts/python.exe backend/generer_kit.py
"""

import sys
import io
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from PIL import Image
from playwright.sync_api import sync_playwright

from generer_copy import generer_copy   # Claude : brief -> copy structuré

sys.stdout.reconfigure(encoding="utf-8")

DOSSIER = Path(__file__).resolve().parent       # backend/
RACINE = DOSSIER.parent                          # racine du projet
TEMPLATES = DOSSIER / "bannieres"                # gabarits de bannières (.j2)
SORTIE = RACINE / "output" / "kit"
SORTIE.mkdir(parents=True, exist_ok=True)

env = Environment(loader=FileSystemLoader(str(TEMPLATES)))

# Formats à produire (nom, largeur, hauteur).
FORMATS = [
    # Meta
    ("meta_1080x1080", 1080, 1080),
    ("meta_1080x1350", 1080, 1350),
    ("meta_1080x1920", 1080, 1920),
    # Google Display
    ("display_300x250", 300, 250),
    ("display_160x600", 160, 600),
    ("display_728x90", 728, 90),     # court -> disposition en ligne
    ("display_320x50", 320, 50),     # court -> disposition en ligne
    # Google Pmax (tailles standard)
    ("pmax_paysage_1200x628", 1200, 628),
    ("pmax_carre_1200x1200", 1200, 1200),
    ("pmax_portrait_960x1200", 960, 1200),
    # Site (dimensions exactes communiquées par le client)
    ("site_header_hp_desktop", 1900, 456),
    ("site_header_hp_mobile", 426, 575),                # portrait
    ("site_bandeau_categorie", 2560, 280),              # bande unique (pas de version mobile, confirmé client)
]

# Champs texte du copy injectés dans les gabarits (categorie/cta servent ailleurs).
CHAMPS_GABARIT = ("titre", "offre_label", "offre_nombre", "offre_suffixe")

# Fonds foncés de la charte (texte et bouton clairs) ; les autres sont clairs.
FONDS_FONCES = {"#253081", "#040c4d"}

# Banque d'images par catégorie (fournie par le client).
ASSETS_CAT = RACINE / "assets" / "produit" / "catégorie"

# Images des opérations transverses (ex. Black Friday), déposées par le marketing
# dans assets/produit/transverses : un fond de bandeau (bandeau.*), une promo par
# défaut (promo par défaut.*), et un sous-dossier par thème contenant son visuel.
TRANSVERSE = RACINE / "assets" / "produit" / "transverses"

# Logos (charte 5). Pas de logo sur les bannières site (on y est déjà). Le logo
# est choisi selon le fond : bleu/jaune sur fond foncé, bleu sur fond clair. Les
# fichiers fournis ayant un fond blanc opaque, on génère et met en cache une
# version transparente de chacun pour qu'ils se posent proprement sur le fond.
LOGOS = RACINE / "assets" / "logo"
LOGOS_CACHE = RACINE / "output" / "_logos"


def _image_categorie(categorie: str, sous_dossier: str):
    """URI file:// de l'image d'une catégorie (ou None si absente / transversale)."""
    dossier = ASSETS_CAT / categorie / sous_dossier
    if not dossier.is_dir():
        return None
    images = sorted(dossier.glob("*.webp"))
    return images[0].resolve().as_uri() if images else None


_EXT_IMG = {".png", ".jpg", ".jpeg", ".webp"}


def themes_transverses():
    """Noms des sous-dossiers de thèmes transverses (ex. 'black friday')."""
    if not TRANSVERSE.is_dir():
        return []
    return sorted(d.name for d in TRANSVERSE.iterdir() if d.is_dir())


def _premiere_image(dossier: Path):
    """URI file:// de la première image d'un dossier (ou None)."""
    if not dossier.is_dir():
        return None
    images = sorted(p for p in dossier.iterdir() if p.suffix.lower() in _EXT_IMG)
    return images[0].resolve().as_uri() if images else None


def _fichier_transverse(stem: str):
    """URI file:// du fichier transverses/<stem>.<ext> (ex. 'bandeau',
    'promo par défaut'), quelle que soit l'extension. None si absent."""
    if not TRANSVERSE.is_dir():
        return None
    for p in sorted(TRANSVERSE.iterdir()):
        if p.is_file() and p.stem.lower() == stem.lower() and p.suffix.lower() in _EXT_IMG:
            return p.resolve().as_uri()
    return None


def _image_theme_transverse(theme: str):
    """Visuel d'un thème transverse (sous-dossier, ex. 'black friday'). None sinon."""
    return _premiere_image(TRANSVERSE / theme) if theme else None


# Variante de logo selon le fond, et mode de détourage du fond blanc :
#   "cle"  = retirer tout le blanc (logo bleu, sans texte blanc à préserver) ;
#   "bord" = retirer le blanc extérieur seulement (garde le texte blanc du badge).
_LOGO_VARIANTES = {
    "clair": ("gefradis-logo-bleu-blanc.png", "cle"),
    "fonce": ("gefradis-logo-bleu-jaune.png", "bord"),
}


def _logo_transparent(src_name: str, mode: str):
    """Chemin d'une version à fond transparent du logo (générée puis mise en cache)."""
    dst = LOGOS_CACHE / src_name
    if dst.exists():
        return dst
    from PIL import Image, ImageDraw
    LOGOS_CACHE.mkdir(parents=True, exist_ok=True)
    if mode == "cle":
        im = Image.open(LOGOS / src_name).convert("RGBA")
        im.putdata([(r, g, b, 0) if r > 235 and g > 235 and b > 235 else (r, g, b, a)
                    for (r, g, b, a) in im.getdata()])
    else:  # "bord" : remplir le blanc extérieur depuis les quatre coins
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
    """Logo (URI file://) choisi selon le fond, ou None sur les bannières site."""
    if nom.startswith("site_"):
        return None
    src, mode = _LOGO_VARIANTES["fonce" if fonce else "clair"]
    return _logo_transparent(src, mode).resolve().as_uri()


def _images_montage(largeur: int):
    """Opération transversale : images 'Bandeau page catégorie' de plusieurs
    catégories, à afficher côte à côte. Le nombre s'adapte à la largeur."""
    cats = sorted(d.name for d in ASSETS_CAT.iterdir() if d.is_dir())
    uris = [u for u in (_image_categorie(c, "Bandeau page catégorie") for c in cats) if u]
    if not uris:
        return []
    # Nombre d'images selon la largeur, pour éviter des bandes trop étroites.
    n = max(2, min(len(uris), round(largeur / 450)))
    return uris[:n]


# Met le contenu d'un gabarit "fin" à l'échelle pour qu'il tienne EXACTEMENT dans
# le cadre (mesure le bloc .contenu, applique transform: scale). Sans effet sur les
# gabarits qui n'ont pas de .contenu.
_AJUSTER_ECHELLE = """() => {
  const b = document.querySelector('.banniere');
  if (!b) return;
  // Gabarits "fins" : on met le bloc .contenu à l'échelle pour qu'il rentre pile.
  const c = document.querySelector('.contenu');
  if (c) {
    c.style.transform = 'none';
    const s = Math.min((b.clientWidth - 16) / c.offsetWidth,
                       (b.clientHeight - 10) / c.offsetHeight, 2.0);
    c.style.transform = 'scale(' + s + ')';
    return;
  }
  // Autres gabarits : si le titre fait deborder, on reduit sa taille jusqu'a ce
  // que tout rentre (filet de securite, quel que soit le format ou le texte).
  const t = document.querySelector('.titre');
  if (!t) return;
  let fs = parseFloat(getComputedStyle(t).fontSize);
  const min = fs * 0.4;   // garde-fou : ne pas reduire le titre sous 40% (lisibilite)
  let guard = 0;
  while ((b.scrollHeight > b.clientHeight + 1 || b.scrollWidth > b.clientWidth + 1)
         && fs > min && guard < 80) {
    fs -= 2; guard++;
    t.style.fontSize = fs + 'px';
  }
}"""


# Animation (étape 5) : apparition progressive (message -> + offre -> + bouton),
# assemblée en GIF. On masque/affiche par "visibility" pour éviter tout décalage de
# mise en page entre les images (les éléments apparaissent sans bouger le reste).
_SEL_OFFRE = ".offre, .offre-label, .prix, .offre-texte, .pastille"
_SEL_CTA = ".cta"
_VISIBILITE = "([sel, v]) => document.querySelectorAll(sel).forEach(e => e.style.visibility = v)"


def _rendre_gif(page, chemin: str):
    """Capture 3 états de la bannière (message seul, + offre, + bouton) et les
    assemble en GIF en boucle. À appeler une fois la bannière rendue et mise à
    l'échelle (la visibility ne déclenche pas de recalcul de mise en page)."""
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


def generer_kit(copy: dict, formats=FORMATS, display_statique=True, display_anime=True):
    """Rend tous les formats du kit à partir d'un copy structuré (dict).

    Pour les formats Google Display, on produit la version statique (PNG) et/ou la
    version animée (GIF), selon display_statique / display_anime."""
    # On repart d'un dossier propre : on retire les PNG/GIF d'un éventuel kit
    # précédent, sinon d'anciens formats resteraient dans l'aperçu et le zip.
    for ancien in list(SORTIE.glob("*.png")) + list(SORTIE.glob("*.gif")):
        ancien.unlink()
    fond = copy.get("couleur_fond") or "#253081"          # défaut : bleu d'origine
    fonce = fond.lower() in FONDS_FONCES
    contexte = {
        **{champ: copy[champ] for champ in CHAMPS_GABARIT},
        "offre_type": copy.get("offre_type", "montant"),   # montant / pourcentage / texte
        "offre_texte": copy.get("offre_texte", ""),
        "offre_pastille": copy.get("offre_pastille", False),  # remise en pastille de coin
        "cta": copy.get("cta", ""),                        # vide -> pas de bouton
        "couleur_fond": fond,
        "couleur_texte": "#ffffff" if fonce else "#040c4d",
        # bouton : contraste avec le fond, couleurs de la charte uniquement
        "couleur_bouton": "#ffffff" if fonce else "#253081",
        "couleur_bouton_texte": "#253081" if fonce else "#ffffff",
    }

    gabarit_colonne = env.get_template("banniere_pub.html.j2")        # carré / vertical
    gabarit_large = env.get_template("banniere_pub_large.html.j2")    # très large
    gabarit_site = env.get_template("banniere_site.html.j2")          # bandeau catégorie
    gabarit_header = env.get_template("banniere_header.html.j2")      # header d'accueil (hero)
    gabarit_pub_image = env.get_template("banniere_pub_image.html.j2")  # pub illustrée
    gabarit_fin = env.get_template("banniere_pub_fin.html.j2")        # formats fins (728x90, 320x50)
    categorie = copy.get("categorie", "transversale")
    # Image pour les pubs, seulement si 1.3 a demandé d'illustrer. Opération
    # transversale : on prend l'image ponctuelle fournie (assets/transverse) ;
    # sinon l'image "promo" de la catégorie.
    if copy.get("illustrer"):
        if categorie == "transversale":
            # visuel du thème détecté (ex. Black Friday), sinon promo par défaut
            image_promo = (_image_theme_transverse(copy.get("theme_transverse", ""))
                           or _fichier_transverse("promo par défaut"))
        else:
            image_promo = _image_categorie(categorie, "promo")
    else:
        image_promo = None
    tmp = TEMPLATES / "_rendu_tmp.html"

    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        for nom, largeur, hauteur in formats:
            logo = _logo_uri(nom, fonce)   # choisi selon le fond ; None pour le site
            if nom.startswith("site_bandeau_categorie"):
                # Bandeau catégorie : image d'ambiance en fond + carte bleue. Pour
                # une opération transversale, on prend l'image ponctuelle fournie
                # (ex. Black Friday) si elle existe, sinon un montage de catégories.
                base = round(hauteur * 0.13, 2)
                evenement = None
                if categorie == "transversale":
                    # fond dédié au transverse (sinon repli sur le montage), + visuel
                    # d'événement posé à côté de la carte si un thème correspond.
                    bg = _fichier_transverse("bandeau")
                    image = bg
                    montage = None if bg else _images_montage(largeur)
                    evenement = _image_theme_transverse(copy.get("theme_transverse", ""))
                else:
                    image, montage = _image_categorie(categorie, "Bandeau page catégorie"), None
                html = gabarit_site.render(
                    largeur=largeur, hauteur=hauteur, base=base,
                    image_uri=image, montage_images=montage, evenement_uri=evenement,
                    avec_cta=False, **contexte
                )
            elif nom.startswith("site_header_hp"):
                # Header d'accueil (hero) : grand message + offre (et produit si
                # demandé). En ligne si large, en colonne si étroit (mobile). Base
                # sur la plus petite dimension pour ne pas surdimensionner en portrait.
                base = round(min(largeur, hauteur) * 0.16, 2)
                sens = "row" if largeur / hauteur >= 2.4 else "column"
                html = gabarit_header.render(
                    largeur=largeur, hauteur=hauteur, base=base, sens=sens,
                    image_uri=image_promo, **contexte
                )
            elif hauteur < 120:
                # Format fin (728x90, 320x50) -> gabarit dédié, mis à l'échelle par JS
                # pour que tout tienne (pas d'image : pas la place sur ces formats).
                html = gabarit_fin.render(
                    largeur=largeur, hauteur=hauteur, logo_uri=logo, **contexte
                )
            elif image_promo:
                # Pub illustrée (1.3 a demandé une image) : produit détouré DANS le cadre.
                base = round(min(largeur, hauteur) * 0.10, 2)
                sens = "row" if largeur >= hauteur else "column"
                html = gabarit_pub_image.render(
                    largeur=largeur, hauteur=hauteur, base=base, sens=sens,
                    image_uri=image_promo, logo_uri=logo, **contexte
                )
            else:
                # Carré / vertical -> disposition EN COLONNE.
                base = round(min(largeur, hauteur) * 0.085, 2)
                # Très vertical -> on répartit sur la hauteur ; sinon on centre.
                justify = "space-evenly" if hauteur / largeur >= 1.4 else "center"
                html = gabarit_colonne.render(
                    largeur=largeur, hauteur=hauteur, base=base, justify=justify,
                    logo_uri=logo, **contexte
                )
            tmp.write_text(html, encoding="utf-8")
            page = navigateur.new_page(
                viewport={"width": largeur, "height": hauteur},
                device_scale_factor=1,
            )
            page.goto(tmp.as_uri())
            page.evaluate("document.fonts.ready")
            page.evaluate(_AJUSTER_ECHELLE)
            est_display = nom.startswith("display_")   # seuls les Display ont une version animée
            if not est_display or display_statique:
                page.locator(".banniere").screenshot(path=str(SORTIE / f"{nom}.png"))
            if est_display and display_anime:
                _rendre_gif(page, str(SORTIE / f"{nom}.gif"))
            page.close()
            print(f"Généré : {nom}  ({largeur}x{hauteur})")
        navigateur.close()

    tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    # Le brief saisi par le marketing (demain : le formulaire de l'interface).
    BRIEF_MARKETING = {
        "operation": "Les jours Gros projets = Grosses Remises",
        "message": "Récompenser les gros projets de rénovation.",
        "mecanique": "100 € offerts dès 1000 € d'achat HT, jusqu'à 500 € offerts.",
        "categorie": "transversale",
    }

    print("Génération du copy via Claude...")
    copy = generer_copy(BRIEF_MARKETING, themes=themes_transverses())
    print(json.dumps(copy, ensure_ascii=False, indent=2))
    print("-" * 70)

    generer_kit(copy)
    print("Kit complet dans :", SORTIE)
