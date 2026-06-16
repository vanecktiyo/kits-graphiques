"""
ÉTAPE 3 - Brancher Claude : du brief créatif au texte structuré.

Le marketing rédige un brief créatif en trois parties (cf. cahier des charges) :
  1.1 mécanique commerciale, 1.2 message commercial, 1.3 illustrations.
Claude joue le rôle de concepteur-rédacteur (copywriter) de Gefradis et renvoie
un JSON structuré : accroche, offre, appel à l'action, catégorie (DÉDUITE) et
variante de style. Le code injecte ensuite ce JSON dans les gabarits (generer_kit).

Point clé d'architecture : Claude génère UNIQUEMENT du texte (le JSON), jamais le
HTML/CSS. La charte VISUELLE vit dans les gabarits ; ici on porte la charte
ÉDITORIALE (contexte de marque + ton) via le prompt système.

Pour garantir un JSON propre, on utilise le "tool use" : on impose à Claude de
répondre via un outil dont on décrit le schéma. Pas de texte à parser à la main.

Lancer :  .venv/Scripts/python.exe backend/generer_copy.py
"""

import sys
import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")   # accents et € corrects à la console (Windows)

RACINE = Path(__file__).resolve().parent.parent
load_dotenv(RACINE / ".env")               # charge ANTHROPIC_API_KEY depuis .env

MODELE = "claude-opus-4-8"

# ---------------------------------------------------------------------------
# Prompt système : QUI est Gefradis (charte 4) + COMMENT on parle (charte 6).
# Volontairement condensé : on garde les consignes qui portent, pas le remplissage.
# ---------------------------------------------------------------------------
SYSTEME = """Tu es le concepteur-rédacteur (copywriter) de Gefradis.

CONTEXTE DE MARQUE (charte 4).
Gefradis est un fabricant français de menuiseries PVC sur-mesure (fenêtres,
portes, porte-fenêtres, volets, portails). Basé à Dunkerque depuis 1996. Vente en
direct d'usine, sans intermédiaire, pour les particuliers et les professionnels.
Arguments clés : prix d'usine, fabrication française, sur-mesure, près de 30 ans
d'expertise.

TON (charte 6).
Professeur ou mentor : précis, professionnel, clair sans être trop technique.
Transparence et pédagogie. Pas de superlatifs creux ni de langage agressif.

PALETTE (charte 1) — couleurs de fond autorisées, n'en sors JAMAIS :
#253081 (St Patricks blue, bleu impactant), #040c4d (Midnight blue, très foncé),
#e7e9f4 (Ghost white, clair doux), #f3f4f6 (Cultured, clair neutre),
#e4e4e4 (Platinum, gris clair), #f9fafb (Cultured 2, presque blanc),
#fffde5 (Beige, clair chaud). L'accent jaune #ffd52b est géré par le gabarit.

TA MISSION.
À partir du brief créatif (mécanique commerciale, message commercial,
illustrations souhaitées), rédige le texte d'une bannière (accroche, libellé et
montant de l'offre) et choisis la couleur de fond.

CONTRAINTES.
- L'accroche (titre) doit être COURTE (3 à 6 mots) : le même message servira sur
  tous les formats, du grand au tout petit. Ne propose qu'UNE version.
- N'invente JAMAIS de chiffre : n'utilise que les montants et conditions du brief.
- Choisis "offre_type" : "montant" (somme en €), "pourcentage" (remise en %), ou
  "texte" (offre non chiffrée). Pour montant/pourcentage, remplis offre_nombre +
  offre_suffixe (offre_texte vide). Pour texte, remplis offre_texte (court) et
  laisse offre_nombre/offre_suffixe vides.
- Déduis la catégorie visée à partir de l'offre (mécanique/message), parmi :
  Fenêtres, Portes, Volets roulants, Volets battants, Portails, Clôtures,
  Portes de garage, Baies vitrées. Mets "transversale" si l'opération porte sur
  tout le catalogue.
- Choisis "couleur_fond" dans la PALETTE, selon le style décrit en 1.3
  (illustrations). Si 1.3 ne précise aucun style, utilise #253081 par défaut.
- Ne renseigne "cta" (texte du bouton d'action) QUE si le brief (1.3) le demande
  explicitement (ex. « bouton CTA "J'en profite" »). Sinon, laisse-le vide ("").
- Mets "illustrer" à true UNIQUEMENT si le brief (1.3) demande d'illustrer avec une
  image ; sinon false.
- Réponds UNIQUEMENT via l'outil fourni."""

# ---------------------------------------------------------------------------
# Schéma de sortie imposé à Claude (tool use). Chaque champ alimentera un gabarit.
# ---------------------------------------------------------------------------
OUTIL = {
    "name": "produire_copy",
    "description": "Produit le texte structuré d'une bannière Gefradis.",
    "input_schema": {
        "type": "object",
        "properties": {
            "categorie": {
                "type": "string",
                "enum": ["Fenêtres", "Portes", "Volets roulants", "Volets battants",
                         "Portails", "Clôtures", "Portes de garage", "Baies vitrées",
                         "transversale"],
                "description": "Catégorie produit visée, DÉDUITE de l'offre, parmi la "
                               "liste ; 'transversale' si toutes les catégories.",
            },
            "titre": {
                "type": "string",
                "description": "Accroche courte et percutante (3 à 6 mots idéalement).",
            },
            "offre_type": {
                "type": "string",
                "enum": ["montant", "pourcentage", "texte"],
                "description": "Type d'offre : 'montant' (ex : 500 €), 'pourcentage' "
                               "(ex : -26 %), ou 'texte' (offre non chiffrée).",
            },
            "offre_label": {
                "type": "string",
                "description": "Libellé devant l'offre (ex : 'à partir de', 'Jusqu'à'). "
                               "Peut être vide.",
            },
            "offre_nombre": {
                "type": "string",
                "description": "Pour montant/pourcentage : le nombre mis en avant, "
                               "chiffres uniquement (ex : '500', '639', '26'). Sinon vide.",
            },
            "offre_suffixe": {
                "type": "string",
                "description": "Pour montant/pourcentage : ce qui suit le nombre "
                               "(ex : '€ offerts', ',85€', '%'). Sinon vide.",
            },
            "offre_texte": {
                "type": "string",
                "description": "Pour le type 'texte' uniquement : l'offre en toutes "
                               "lettres, COURTE (ex : 'Livraison offerte'). Sinon vide.",
            },
            "cta": {
                "type": "string",
                "description": "Texte du bouton d'action, UNIQUEMENT si le brief (1.3) "
                               "le demande ; sinon chaîne vide.",
            },
            "couleur_fond": {
                "type": "string",
                "enum": ["#253081", "#040c4d", "#e7e9f4", "#f3f4f6",
                         "#e4e4e4", "#f9fafb", "#fffde5"],
                "description": "Couleur de fond choisie dans la palette de la charte, "
                               "selon le style décrit en 1.3 (#253081 par défaut).",
            },
            "illustrer": {
                "type": "boolean",
                "description": "true UNIQUEMENT si le brief (1.3) demande d'illustrer "
                               "avec une image ; sinon false. N'affecte que les pubs.",
            },
        },
        "required": [
            "categorie", "titre", "offre_type", "offre_label", "offre_nombre",
            "offre_suffixe", "offre_texte", "cta", "couleur_fond", "illustrer",
        ],
    },
}

_client = anthropic.Anthropic()   # lit ANTHROPIC_API_KEY dans l'environnement


def _prompt_utilisateur(brief: dict) -> str:
    """Met en forme le brief créatif (1.1, 1.2, 1.3) saisi par le marketing."""
    return (
        f"1.1 Mécanique commerciale : {brief.get('mecanique', '')}\n"
        f"1.2 Message commercial : {brief.get('message', '')}\n"
        f"1.3 Illustrations souhaitées : "
        f"{brief.get('illustrations') or 'non précisé (charte Gefradis par défaut)'}"
    )


def generer_copy(brief: dict) -> dict:
    """Envoie le brief à Claude et renvoie le copy structuré (dict)."""
    reponse = _client.messages.create(
        model=MODELE,
        max_tokens=600,
        system=SYSTEME,
        tools=[OUTIL],
        tool_choice={"type": "tool", "name": "produire_copy"},
        messages=[{"role": "user", "content": _prompt_utilisateur(brief)}],
    )
    # Avec tool_choice forcé, la réponse contient un bloc "tool_use" : son champ
    # .input EST notre JSON, déjà validé contre le schéma.
    for bloc in reponse.content:
        if bloc.type == "tool_use":
            return bloc.input
    raise RuntimeError("Claude n'a pas renvoyé d'appel d'outil.")


if __name__ == "__main__":
    # Deux briefs de test : une opération transversale + une opération catégorie.
    BRIEFS_TEST = [
        {
            "mecanique": "Remise conditionnée au montant d'achat : 100 € dès 1000 € HT, "
                         "jusqu'à 500 € offerts. Valable sur tout le catalogue.",
            "message": "Opération « Les jours Gros projets = Grosses Remises ». "
                       "Jusqu'à 500 € offerts sur votre commande.",
            "illustrations": "",
        },
        {
            "mecanique": "Offre limitée à la famille portes d'entrée, à partir de 639,85 €.",
            "message": "Vos portes d'entrée sur-mesure, au prix d'usine.",
            "illustrations": "visuels de portes d'entrée",
        },
    ]

    for i, brief in enumerate(BRIEFS_TEST, 1):
        print("=" * 70)
        print(f"BRIEF {i}")
        copy = generer_copy(brief)
        print(json.dumps(copy, ensure_ascii=False, indent=2))
    print("=" * 70)
