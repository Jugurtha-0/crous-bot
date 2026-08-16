import json
import os


FICHIER_ETAT = "etat_logements.json"


def charger_etats():
    if not os.path.exists(FICHIER_ETAT):
        return {}

    try:
        with open(FICHIER_ETAT, "r", encoding="utf-8") as fichier:
            return json.load(fichier)

    except (json.JSONDecodeError, OSError):
        return {}


def sauvegarder_etats(etats):
    with open(FICHIER_ETAT, "w", encoding="utf-8") as fichier:
        json.dump(
            etats,
            fichier,
            ensure_ascii=False,
            indent=2
        )
        