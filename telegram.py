import json
import os

import requests
from dotenv import load_dotenv

from abonnes import charger_abonnes

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

# Chat_id de l'administrateur (toi) : reçoit toujours les alertes,
# même sans être dans la liste des abonnés payants.
ADMIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def envoyer_message_simple(chat_id, texte, boutons=None):
    """
    Envoie un message texte simple à un chat_id donné.
    `boutons` est une liste optionnelle de dicts {"text": ..., "url": ...}.
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
    Envoie l'alerte de disponibilité à tous les abonnés actifs,
    plus à l'administrateur (toujours, même hors liste).
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

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    destinataires = {a["chat_id"] for a in charger_abonnes()}

    if ADMIN_CHAT_ID:
        destinataires.add(int(ADMIN_CHAT_ID))

    for chat_id in destinataires:

        try:
            response = requests.post(
                url,
                data={
                    "chat_id": chat_id,
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
            print(f"❌ Échec d'envoi à {chat_id} : {erreur}")
