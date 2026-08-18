"""
Gestion de la liste blanche des abonnés.

Stockage : le fichier abonnes.json est lu/écrit directement dans le
dépôt GitHub via l'API GitHub, PAS sur le disque local du serveur.
C'est nécessaire car le disque de Render (plan Free) est éphémère :
tout fichier écrit localement est perdu au moindre redémarrage.

Variables d'environnement nécessaires (à ajouter dans Render) :
  GITHUB_TOKEN : un Personal Access Token GitHub avec la permission
                 "Contents: Read and write" sur le dépôt du bot.
  GITHUB_REPO  : le nom du dépôt, au format "utilisateur/nom-du-repo"
                 (ex : "Jugurtha-0/crous-bot")

Si ces variables sont absentes (ex : test en local sur ton PC), le
script bascule automatiquement sur un fichier local abonnes.json —
pratique pour tester, mais NON persistant sur Render Free.
"""

import base64
import json
import os

import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
CHEMIN_FICHIER = "abonnes.json"

FICHIER_LOCAL = "abonnes.json"

_utilise_github = bool(GITHUB_TOKEN and GITHUB_REPO)

if not _utilise_github:
    print(
        "⚠️ GITHUB_TOKEN / GITHUB_REPO absents : la liste des abonnés "
        "est stockée localement, donc PAS persistante sur Render Free."
    )


def _headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "crous-bot",
    }


def _url():
    return f"https://api.github.com/repos/{GITHUB_REPO}/contents/{CHEMIN_FICHIER}"


def charger_abonnes():
    """Retourne la liste des abonnés actifs : [{"chat_id": int, "nom": str}, ...]"""

    if _utilise_github:
        try:
            response = requests.get(_url(), headers=_headers(), timeout=15)

            if response.status_code == 404:
                return []

            response.raise_for_status()
            data = response.json()
            contenu = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(contenu)

        except Exception as erreur:
            print(f"❌ Erreur lecture abonnes.json (GitHub) : {erreur}")
            return []

    if not os.path.exists(FICHIER_LOCAL):
        return []

    try:
        with open(FICHIER_LOCAL, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def sauvegarder_abonnes(abonnes):

    if _utilise_github:

        contenu_str = json.dumps(abonnes, ensure_ascii=False, indent=2)
        contenu_b64 = base64.b64encode(contenu_str.encode("utf-8")).decode("utf-8")

        # Il faut le sha du fichier existant pour pouvoir l'écraser.
        sha = None
        try:
            response = requests.get(_url(), headers=_headers(), timeout=15)
            if response.status_code == 200:
                sha = response.json()["sha"]
        except Exception:
            pass

        payload = {
            "message": "Mise à jour de la liste des abonnés",
            "content": contenu_b64,
        }
        if sha:
            payload["sha"] = sha

        response = requests.put(
            _url(), headers=_headers(), json=payload, timeout=15
        )
        response.raise_for_status()
        return

    with open(FICHIER_LOCAL, "w", encoding="utf-8") as f:
        json.dump(abonnes, f, ensure_ascii=False, indent=2)


def ajouter_abonne(chat_id, nom=""):
    abonnes = charger_abonnes()

    if any(a["chat_id"] == chat_id for a in abonnes):
        print(f"⚠️ {chat_id} est déjà abonné.")
        return

    abonnes.append({"chat_id": chat_id, "nom": nom})
    sauvegarder_abonnes(abonnes)
    print(f"✅ {chat_id} ({nom}) ajouté aux abonnés.")


def retirer_abonne(chat_id):
    abonnes = charger_abonnes()
    nouveaux = [a for a in abonnes if a["chat_id"] != chat_id]

    if len(nouveaux) == len(abonnes):
        print(f"⚠️ {chat_id} n'était pas dans la liste.")
        return

    sauvegarder_abonnes(nouveaux)
    print(f"🗑️ {chat_id} retiré des abonnés.")


def est_abonne(chat_id):
    abonnes = charger_abonnes()
    return any(a["chat_id"] == chat_id for a in abonnes)
