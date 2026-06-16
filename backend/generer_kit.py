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
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
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
    # Site (dimensions à confirmer auprès du client)
    ("site_header_hp_desktop", 1920, 500),
    ("site_header_hp_mobile", 768, 420),
    ("site_bandeau_categorie_desktop", 1200, 360),
    ("site_bandeau_categorie_mobile", 768, 300),
]

# Champs texte du copy injectés dans les gabarits (categorie/cta servent ailleurs).
CHAMPS_GABARIT = ("titre", "offre_label", "offre_nombre", "offre_suffixe")

# Fonds foncés de la charte (texte et bouton clairs) ; les autres sont clairs.
FONDS_FONCES = {"#253081", "#040c4d"}

# Banque d'images par catégorie (fournie par le client).
ASSETS_CAT = RACINE / "assets" / "produit" / "catégorie"


def _image_categorie(categorie: str, sous_dossier: str):
    """URI file:// de l'image d'une catégorie (ou None si absente / transversale)."""
    dossier = ASSETS_CAT / categorie / sous_dossier
    if not dossier.is_dir():
        return None
    images = sorted(dossier.glob("*.webp"))
    return images[0].resolve().as_uri() if images else None


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


def generer_kit(copy: dict, formats=FORMATS):
    """Rend tous les formats du kit à partir d'un copy structuré (dict)."""
    fond = copy.get("couleur_fond") or "#253081"          # défaut : bleu d'origine
    fonce = fond.lower() in FONDS_FONCES
    contexte = {
        **{champ: copy[champ] for champ in CHAMPS_GABARIT},
        "offre_type": copy.get("offre_type", "montant"),   # montant / pourcentage / texte
        "offre_texte": copy.get("offre_texte", ""),
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
    # Image "promo" pour les pubs, seulement si 1.3 a demandé d'illustrer.
    image_promo = _image_categorie(categorie, "promo") if copy.get("illustrer") else None
    tmp = TEMPLATES / "_rendu_tmp.html"

    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        for nom, largeur, hauteur in formats:
            if nom.startswith("site_bandeau_categorie"):
                # Bandeau catégorie : image d'ambiance en fond + carte bleue (ou
                # montage de plusieurs catégories si l'opération est transversale).
                base = round(hauteur * 0.13, 2)
                if categorie == "transversale":
                    image, montage = None, _images_montage(largeur)
                else:
                    image, montage = _image_categorie(categorie, "Bandeau page catégorie"), None
                html = gabarit_site.render(
                    largeur=largeur, hauteur=hauteur, base=base,
                    image_uri=image, montage_images=montage, avec_cta=False, **contexte
                )
            elif nom.startswith("site_header_hp"):
                # Header d'accueil (hero) : grand message + offre (et produit si
                # demandé). En ligne si large, en colonne si étroit (mobile).
                base = round(hauteur * 0.16, 2)
                sens = "row" if largeur / hauteur >= 2.4 else "column"
                html = gabarit_header.render(
                    largeur=largeur, hauteur=hauteur, base=base, sens=sens,
                    image_uri=image_promo, **contexte
                )
            elif hauteur < 120:
                # Format fin (728x90, 320x50) -> gabarit dédié, mis à l'échelle par JS
                # pour que tout tienne (pas d'image : pas la place sur ces formats).
                html = gabarit_fin.render(
                    largeur=largeur, hauteur=hauteur, **contexte
                )
            elif image_promo:
                # Pub illustrée (1.3 a demandé une image) : produit détouré DANS le cadre.
                base = round(min(largeur, hauteur) * 0.10, 2)
                sens = "row" if largeur >= hauteur else "column"
                html = gabarit_pub_image.render(
                    largeur=largeur, hauteur=hauteur, base=base, sens=sens,
                    image_uri=image_promo, **contexte
                )
            else:
                # Carré / vertical -> disposition EN COLONNE.
                base = round(min(largeur, hauteur) * 0.085, 2)
                # Très vertical -> on répartit sur la hauteur ; sinon on centre.
                justify = "space-evenly" if hauteur / largeur >= 1.4 else "center"
                html = gabarit_colonne.render(
                    largeur=largeur, hauteur=hauteur, base=base, justify=justify, **contexte
                )
            tmp.write_text(html, encoding="utf-8")
            page = navigateur.new_page(
                viewport={"width": largeur, "height": hauteur},
                device_scale_factor=1,
            )
            page.goto(tmp.as_uri())
            page.evaluate("document.fonts.ready")
            page.evaluate(_AJUSTER_ECHELLE)
            page.locator(".banniere").screenshot(path=str(SORTIE / f"{nom}.png"))
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
    copy = generer_copy(BRIEF_MARKETING)
    print(json.dumps(copy, ensure_ascii=False, indent=2))
    print("-" * 70)

    generer_kit(copy)
    print("Kit complet dans :", SORTIE)
