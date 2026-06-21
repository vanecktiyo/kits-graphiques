"""
VERSION B (composable) — du brief au copy structuré (Claude).

Identique au copy de la version A : mêmes champs, même charte éditoriale, JSON via
tool use. Claude rédige seulement le texte (accroche, offre, paliers, date) ; l'image,
le bouton et le fond viennent du formulaire. C'est le moteur d'assemblage (generer_kit)
qui range ces éléments dans le gabarit unique et adapte la mise en page à chaque format.

La couleur de fond n'est PAS choisie par Claude : elle vient du formulaire (comme A).
Claude renvoie toujours du JSON, jamais de HTML/CSS.
"""

import sys
import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

RACINE = Path(__file__).resolve().parent.parent       # composable/
load_dotenv(RACINE.parent / ".env")                    # clé API partagée du projet

MODELE = "claude-opus-4-8"

SYSTEME = """Tu es le concepteur-rédacteur (copywriter) et directeur artistique de Gefradis.

CONTEXTE DE MARQUE (charte 4).
Gefradis est un fabricant français de menuiseries PVC sur-mesure (fenêtres, portes,
porte-fenêtres, volets, portails). Basé à Dunkerque depuis 1996. Vente en direct
d'usine, sans intermédiaire. Arguments clés : prix d'usine, fabrication française,
sur-mesure, près de 30 ans d'expertise.

TON (charte 6).
Professeur ou mentor : précis, professionnel, clair sans être trop technique.
Pédagogie et transparence. Pas de superlatifs creux ni de langage agressif.

TA MISSION.
À partir du brief créatif (1.1 mécanique, 1.2 message, 1.3 direction créative), rédige le
texte de la bannière (accroche, offre, paliers, date). L'image, le bouton et la couleur de
fond sont choisis dans le formulaire ; le placement de la remise est géré par le code.

CONTRAINTES.
- L'accroche (titre) doit être COURTE (3 à 6 mots) : le même message sert sur tous les
  formats. Ne propose qu'UNE version. C'est une ACCROCHE (un bénéfice, une idée), JAMAIS la
  simple répétition de l'offre : ne mets PAS le montant/pourcentage/avantage dans le titre.
- N'invente JAMAIS de chiffre : n'utilise que les montants et conditions du brief.
- "offre_type" : "montant", "pourcentage" ou "texte" (offre non chiffrée). Pour
  montant/pourcentage, remplis offre_nombre + offre_suffixe (offre_texte vide). Pour
  texte, remplis offre_texte (court) et laisse offre_nombre/offre_suffixe vides.
- "offre_suffixe" reste TRÈS COURT (ex. '€ offerts', '€', '%'). N'y mets JAMAIS une phrase
  (« sur la motorisation », « par fenêtre », « d'achat »...) : ce complément va dans le
  titre ou le libellé, pas dans le bloc jaune. De même, "offre_texte" reste court (2-3 mots).
- SIGNE des pourcentages : pour une remise en % présentée SEULE (« Jusqu'à 20% »,
  « -20% »), mets le « - » dans offre_nombre (ex. '-20'). PAS de « - » si le message dit
  déjà l'économie (« Économisez 20% », « 20% offerts »).
- Déduis la catégorie visée parmi : Fenêtres, Portes, Volets roulants, Volets battants,
  Portails, Clôtures, Portes de garage, Baies vitrées. "transversale" si tout le catalogue.
- "theme_transverse" : pour une opération transversale uniquement, le thème de la liste
  fournie qui correspond au message (par le sens), écrit EXACTEMENT ; sinon "".
- "paliers" : si la mécanique (1.1) comporte plusieurs PALIERS (2 à 3 max) :
  {condition, valeur}. Sinon vide. Renseigne TOUJOURS aussi l'offre résumé (offre_*) avec
  le montant le plus avantageux (elle sert sur les petits formats).
- "date_validite" : si le brief donne une échéance, écris-la comme une MENTION COMPLÈTE et
  autonome (ex. « Jusqu'au 30 juin 2026 », « Jusqu'à la fin du mois », « Valable jusqu'au
  5 mai »), JAMAIS un fragment isolé (« fin du mois », « 30 juin »). Sinon "".
- Réponds UNIQUEMENT via l'outil fourni."""

OUTIL = {
    "name": "composer_banniere",
    "description": "Produit le texte structuré et la mise en page d'une bannière Gefradis.",
    "input_schema": {
        "type": "object",
        "properties": {
            "categorie": {"type": "string",
                          "enum": ["Fenêtres", "Portes", "Volets roulants", "Volets battants",
                                   "Portails", "Clôtures", "Portes de garage", "Baies vitrées",
                                   "transversale"],
                          "description": "Catégorie produit DÉDUITE ; 'transversale' si tout le catalogue."},
            "titre": {"type": "string", "description": "Accroche courte (3 à 6 mots)."},
            "offre_type": {"type": "string", "enum": ["montant", "pourcentage", "texte"],
                           "description": "'montant', 'pourcentage' ou 'texte' (non chiffré)."},
            "offre_label": {"type": "string", "description": "Libellé devant l'offre (ex. 'Jusqu'à'). Peut être vide."},
            "offre_nombre": {"type": "string",
                             "description": "Nombre mis en avant. Montant : chiffres seuls. "
                                            "Pourcentage présenté SEUL : préfixe '-' (ex. '-20'). "
                                            "Pas de '-' si le message exprime déjà l'économie. Sinon vide."},
            "offre_suffixe": {"type": "string", "description": "Ce qui suit le nombre (ex. '€ offerts', '%'). Sinon vide."},
            "offre_texte": {"type": "string", "description": "Pour le type 'texte' : l'offre en toutes lettres, courte. Sinon vide."},
            "theme_transverse": {"type": "string", "description": "Thème transverse de la liste correspondant au message ; sinon ''."},
            "paliers": {"type": "array",
                        "description": "Paliers de remise (2 à 3 max) si la mécanique en comporte ; sinon vide.",
                        "items": {"type": "object",
                                  "properties": {"condition": {"type": "string"},
                                                 "valeur": {"type": "string"}},
                                  "required": ["condition", "valeur"]}},
            "date_validite": {"type": "string", "description": "Échéance en MENTION COMPLÈTE "
                              "(ex. 'Jusqu'au 30 juin 2026', 'Jusqu'à la fin du mois'), jamais "
                              "un fragment isolé ('fin du mois'). Sinon ''."},
        },
        "required": ["categorie", "titre", "offre_type", "offre_label",
                     "offre_nombre", "offre_suffixe", "offre_texte",
                     "theme_transverse", "paliers", "date_validite"],
    },
}

_client = anthropic.Anthropic()


def _prompt_utilisateur(brief: dict, themes=()) -> str:
    texte = (
        f"1.1 Mécanique commerciale : {brief.get('mecanique', '')}\n"
        f"1.2 Message commercial : {brief.get('message', '')}\n"
        f"1.3 Illustrations souhaitées : "
        f"{brief.get('illustrations') or 'non précisé (charte Gefradis par défaut)'}"
    )
    if themes:
        texte += ("\n\nThèmes transverses disponibles (pour 'theme_transverse', si "
                  "l'opération est transversale) : " + ", ".join(themes) + ".")
    return texte


def composer(brief: dict, themes=()) -> dict:
    """Brief -> copy structuré (dict), via Claude (tool use)."""
    reponse = _client.messages.create(
        model=MODELE, max_tokens=700, system=SYSTEME,
        tools=[OUTIL], tool_choice={"type": "tool", "name": "composer_banniere"},
        messages=[{"role": "user", "content": _prompt_utilisateur(brief, themes)}],
    )
    for bloc in reponse.content:
        if bloc.type == "tool_use":
            return bloc.input
    raise RuntimeError("Claude n'a pas renvoyé d'appel d'outil.")


if __name__ == "__main__":
    BRIEF = {
        "mecanique": "100 € offerts dès 1000 € HT, 350 € dès 3000 €. Tout le catalogue. "
                     "Valable jusqu'au 30 juin 2026.",
        "message": "Opération « Gros projets = Grosses remises ».",
        "illustrations": "une image de nos produits, un bouton « J'en profite »",
    }
    print(json.dumps(composer(BRIEF), ensure_ascii=False, indent=2))
