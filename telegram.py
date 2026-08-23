import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

# Identifiant du canal privé où sont postées les alertes.
# L'accès à ce canal est géré automatiquement par Tribute
# (abonnement payant, ajout/retrait des membres, renouvellement).
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")


def envoyer_message_simple(chat_id, texte, boutons=None):
    """
    Envoie un message texte simple à un chat_id donné
    (utilisé par exemple pour répondre à /start en privé).
    """

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": texte,
        "disable_web_page_preview": True
    }

    if boutons:
        data["reply_markup"] = json.dumps({
            "inline_keyboard": [[b] for b in boutons]
        })

    response = requests.post(url, data=data, timeout=20)
    response.raise_for_status()


def envoyer_telegram(logement):
    """
    Poste l'alerte de disponibilité dans le canal privé.
    Tribute gère qui a le droit d'être membre de ce canal (donc
    qui reçoit réellement le message) — le bot n'a plus besoin de
    connaître la liste des abonnés.
    """

    logement_id = logement["id"]

    lien = (
        "https://trouverunlogement.lescrous.fr/"
        f"tools/47/accommodations/{logement_id}"
    )

    message = (
        "🚨 CROUS — NOUVELLE DISPONIBILITÉ\n\n"
        f"🏠 {logement['residence']}\n"
        f"📍 {logement['ville']}\n\n"
        f"🛏️ {logement['type']}\n"
        f"📐 {logement['surface']} m²\n"
        f"💰 {logement['loyer']} €/mois\n\n"
        "⚡ Disponible maintenant"
    )

    if not CHANNEL_ID:
        print("❌ TELEGRAM_CHANNEL_ID absent : impossible de poster l'alerte.")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            data={
                "chat_id": CHANNEL_ID,
                "text": message,
                "disable_web_page_preview": True,
                "reply_markup": json.dumps({
                    "inline_keyboard": [
                        [
                            {
                                "text": "🏠 Ouvrir le logement",
                                "url": lien
                            }
                        ]
                    ]
                })
            },
            timeout=20
        )
        response.raise_for_status()

    except Exception as erreur:
        print(f"❌ Échec de publication dans le canal : {erreur}")
