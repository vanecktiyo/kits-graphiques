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

TA MISSION.
À partir du brief créatif (mécanique commerciale, message commercial,
illustrations souhaitées), rédige le texte d'une bannière (accroche, libellé et
montant de l'offre). La couleur de fond est choisie ailleurs (dans le formulaire).

CONTRAINTES.
- L'accroche (titre) doit être COURTE (3 à 6 mots) : le même message servira sur
  tous les formats, du grand au tout petit. Ne propose qu'UNE version. C'est une
  ACCROCHE (un bénéfice, une idée), JAMAIS la simple répétition de l'offre : ne mets
  PAS le montant/pourcentage/avantage dans le titre.
- N'invente JAMAIS de chiffre : n'utilise que les montants et conditions du brief.
- "offre_suffixe" reste TRÈS COURT (ex. '€ offerts', '€', '%'). N'y mets JAMAIS une
  phrase (« sur la motorisation », « par fenêtre », « d'achat »...) : ce complément va
  dans le titre ou le libellé, pas dans le bloc jaune. "offre_texte" reste court (2-3 mots).
- Choisis "offre_type" : "montant" (somme en €), "pourcentage" (remise en %), ou
  "texte" (offre non chiffrée). Pour montant/pourcentage, remplis offre_nombre +
  offre_suffixe (offre_texte vide). Pour texte, remplis offre_texte (court) et
  laisse offre_nombre/offre_suffixe vides.
- SIGNE des pourcentages : pour une remise en % présentée SEULE (« Jusqu'à 20% »,
  « -20% », sans verbe), écris offre_nombre avec le « - » (ex. '-20'). N'mets PAS le
  « - » si le message dit déjà l'économie (« Économisez 20% », « 20% offerts »).
- Déduis la catégorie visée à partir de l'offre (mécanique/message), parmi :
  Fenêtres, Portes, Volets roulants, Volets battants, Portails, Clôtures,
  Portes de garage, Baies vitrées. Mets "transversale" si l'opération porte sur
  tout le catalogue.
- "theme_transverse" : UNIQUEMENT si l'opération est transversale ET qu'un thème de
  la liste fournie (s'il y en a une) correspond au message par le SENS (ex. « Black
  Friday »), renvoie son nom EXACT tel qu'écrit dans la liste ; sinon "" (vide).
- "paliers" : si la mécanique (1.1) comporte plusieurs PALIERS de remise (ex. 100 €
  dès 1000 € d'achat, 350 € dès 3000 €), liste-les (2 à 3 max) : {condition, valeur}.
  Sinon laisse vide. Renseigne TOUJOURS aussi l'offre résumé (offre_*) avec le montant
  le plus avantageux (elle sert sur les petits formats).
- "date_validite" : si le brief donne une échéance, écris-la comme une MENTION COMPLÈTE et
  autonome (ex. « Jusqu'au 30 juin 2026 », « Jusqu'à la fin du mois »), JAMAIS un fragment
  isolé (« fin du mois », « 30 juin »). Sinon "".
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
                "description": "Le nombre mis en avant. Montant : chiffres seuls "
                               "(ex : '500', '639'). Pourcentage de remise présenté SEUL "
                               "(libellé « Jusqu'à », « Remise de », ou sans libellé) : "
                               "préfixe par '-' (ex : '-20', '-26'). PAS de '-' si le "
                               "message exprime déjà l'économie (« Économisez 20% », "
                               "« 20% offerts »). Sinon vide.",
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
            "theme_transverse": {
                "type": "string",
                "description": "Pour une opération transversale uniquement : le thème "
                               "de la liste fournie qui correspond au message (par le "
                               "sens), écrit EXACTEMENT comme dans la liste ; sinon ''.",
            },
            "paliers": {
                "type": "array",
                "description": "Paliers de remise SI la mécanique (1.1) en comporte "
                               "plusieurs (2 à 3 max) ; sinon liste vide.",
                "items": {
                    "type": "object",
                    "properties": {
                        "condition": {"type": "string",
                                      "description": "Le seuil, ex. 'Dès 1000 € d'achat'."},
                        "valeur": {"type": "string",
                                   "description": "L'avantage, ex. '100 € offerts'."},
                    },
                    "required": ["condition", "valeur"],
                },
            },
            "date_validite": {
                "type": "string",
                "description": "Échéance en MENTION COMPLÈTE (ex. 'Jusqu'au 30 juin 2026', "
                               "'Jusqu'à la fin du mois'), jamais un fragment isolé "
                               "('fin du mois'). Sinon ''.",
            },
        },
        "required": [
            "categorie", "titre", "offre_type", "offre_label", "offre_nombre",
            "offre_suffixe", "offre_texte",
            "theme_transverse", "paliers", "date_validite",
        ],
    },
}

_client = anthropic.Anthropic()   # lit ANTHROPIC_API_KEY dans l'environnement


def _prompt_utilisateur(brief: dict, themes=()) -> str:
    """Met en forme le brief créatif (1.1, 1.2, 1.3) saisi par le marketing."""
    texte = (
        f"1.1 Mécanique commerciale : {brief.get('mecanique', '')}\n"
        f"1.2 Message commercial : {brief.get('message', '')}\n"
        f"1.3 Illustrations souhaitées : "
        f"{brief.get('illustrations') or 'non précisé (charte Gefradis par défaut)'}"
    )
    if themes:
        texte += ("\n\nThèmes transverses disponibles (pour 'theme_transverse', "
                  "si l'opération est transversale) : " + ", ".join(themes) + ".")
    return texte


def generer_copy(brief: dict, themes=()) -> dict:
    """Envoie le brief à Claude et renvoie le copy structuré (dict).

    `themes` : noms des thèmes transverses disponibles (sous-dossiers d'images),
    pour que Claude choisisse le bon visuel d'une opération transversale."""
    reponse = _client.messages.create(
        model=MODELE,
        max_tokens=600,
        system=SYSTEME,
        tools=[OUTIL],
        tool_choice={"type": "tool", "name": "produire_copy"},
        messages=[{"role": "user", "content": _prompt_utilisateur(brief, themes)}],
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
