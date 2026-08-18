import os
import threading
import time
from datetime import datetime

import requests
from flask import Flask, request

from zone import ZONES
from crous_api import rechercher_logements
from etat_logements import charger_etats, sauvegarder_etats
from detecteur import detecter_changements
from telegram import envoyer_telegram, envoyer_message_simple
from abonnes import est_abonne


CONTACT_ADMIN = "@JIGO_CH"


INTERVALLE = 3 * 60          # vérification CROUS toutes les 3 minutes
INTERVALLE_PING = 10 * 60    # auto-ping toutes les 10 minutes (< 15 min = seuil de mise en veille de Render)

app = Flask(__name__)

derniere_verification = None


def effectuer_verification():

    global derniere_verification

    print("\n" + "=" * 50)
    print("🔍 Vérification :", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("=" * 50)

    anciens_etats = charger_etats()
    tous_les_logements = []
    zones_reussies = 0
    zones_echouees = 0

    for nom_zone, location in ZONES.items():
        print(f"\n🔎 {nom_zone}")
        try:
            logements = rechercher_logements(location)
            print(f"   ✅ {len(logements)} logement(s) trouvé(s)")
            tous_les_logements.extend(logements)
            zones_reussies += 1
        except Exception as erreur:
            zones_echouees += 1
            print(f"   ❌ Erreur API pour {nom_zone} : {erreur}")
            continue

    print(f"\nZones réussies : {zones_reussies} / Zones échouées : {zones_echouees}")

    if zones_reussies == 0:
        print("⚠️ Aucune zone n'a répondu correctement. États précédents conservés.")
        derniere_verification = datetime.now()
        return

    alertes, nouveaux_etats = detecter_changements(anciens_etats, tous_les_logements)
    sauvegarder_etats(nouveaux_etats)

    if alertes:
        print(f"\n🚨 {len(alertes)} nouvelle(s) disponibilité(s) !")
        for logement in alertes:
            try:
                envoyer_telegram(logement)
                print("📱 Telegram envoyé")
            except Exception as erreur:
                print(f"❌ Erreur Telegram : {erreur}")
    else:
        print("\n✅ Aucune nouvelle disponibilité.")

    derniere_verification = datetime.now()


def boucle_surveillance():
    while True:
        try:
            effectuer_verification()
        except Exception as erreur:
            print(f"\n❌ Erreur générale : {erreur}")
        time.sleep(INTERVALLE)


def boucle_auto_ping():
    """
    Fait une requête HTTP vers l'URL publique du service lui-même,
    toutes les INTERVALLE_PING secondes. Cette requête entrante
    réinitialise le compteur d'inactivité de Render et empêche donc
    la mise en veille (qui se déclenche après 15 min sans requête).
    """
    url = os.environ.get("RENDER_EXTERNAL_URL")

    if not url:
        print("ℹ️ RENDER_EXTERNAL_URL absent (pas sur Render) : auto-ping désactivé.")
        return

    while True:
        time.sleep(INTERVALLE_PING)
        try:
            requests.get(url, timeout=10)
            print(f"🔁 Auto-ping envoyé ({datetime.now().strftime('%H:%M:%S')})")
        except Exception as erreur:
            print(f"⚠️ Auto-ping échoué : {erreur}")


@app.route("/")
def health():
    statut = (
        derniere_verification.strftime("%d/%m/%Y %H:%M:%S")
        if derniere_verification
        else "pas encore lancée"
    )
    return f"Bot CROUS actif ✅ — dernière vérification : {statut}", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Reçoit les messages envoyés au bot par les utilisateurs Telegram.
    Ne gère que /start pour l'instant : accueil + explication du
    fonctionnement de la liste blanche manuelle.
    """

    update = request.get_json(silent=True) or {}
    message = update.get("message", {})
    texte = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not chat_id:
        return "ok", 200

    if texte.startswith("/start"):

        if est_abonne(chat_id):
            reponse = (
                "✅ Ton accès est actif !\n\n"
                "Tu recevras une alerte dès qu'un logement CROUS "
                "se libère, partout en France."
            )
        else:
            reponse = (
                "👋 Bienvenue sur CROUS Notif !\n\n"
                "Ce bot t'alerte instantanément dès qu'un logement "
                "CROUS redevient disponible, partout en France.\n\n"
                "💳 Accès : 10€/mois\n\n"
                f"Pour activer ton accès, contacte {CONTACT_ADMIN} "
                "avec ton identifiant ci-dessous :\n\n"
                f"🆔 Ton identifiant : {chat_id}"
            )

        try:
            envoyer_message_simple(chat_id, reponse)
        except Exception as erreur:
            print(f"⚠️ Erreur réponse /start : {erreur}")

    return "ok", 200


if __name__ == "__main__":
    threading.Thread(target=boucle_surveillance, daemon=True).start()
    threading.Thread(target=boucle_auto_ping, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
