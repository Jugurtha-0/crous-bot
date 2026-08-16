import os

import requests
from dotenv import load_dotenv
import json

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def envoyer_telegram(logement):

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

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
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