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


# Lien de paiement Tribute (abonnement au canal privé).
# ⚠️ à compléter dès que tu l'as récupéré depuis @Tribute.
LIEN_PAIEMENT = os.getenv("LIEN_PAIEMENT_TRIBUTE", "https://t.me/tribute/app?startapp=s144z")

# --- Paddle (paiement par carte automatique) ---
PADDLE_PRICE_ID = os.getenv("PADDLE_PRICE_ID", "pri_01m0q2gtcvrrp2399desx4scc5")
PADDLE_CLIENT_TOKEN = os.getenv("PADDLE_CLIENT_TOKEN", "")  # depuis Developer tools > Authentication (préfixe live_ ou test_)
PADDLE_WEBHOOK_SECRET = os.getenv("PADDLE_WEBHOOK_SECRET", "")
PADDLE_ENVIRONMENT = os.getenv("PADDLE_ENVIRONMENT", "sandbox")  # "sandbox" ou "production"

CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "contact@example.com")  # à remplacer par une vraie adresse
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://crous-bot-1dqp.onrender.com")


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
                succes = envoyer_telegram(logement)
                if succes:
                    print("📱 Telegram envoyé")
                else:
                    print("⚠️ Telegram NON envoyé (voir erreur ci-dessus)")
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

    url_status = url.rstrip("/") + "/status"

    while True:
        time.sleep(INTERVALLE_PING)
        try:
            requests.get(url_status, timeout=10)
            print(f"🔁 Auto-ping envoyé ({datetime.now().strftime('%H:%M:%S')})")
        except Exception as erreur:
            print(f"⚠️ Auto-ping échoué : {erreur}")


@app.route("/")
def accueil():
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CROUS Notif — Alertes logement CROUS en temps réel</title>
<meta name="description" content="Reçois une alerte instantanée dès qu'un logement CROUS redevient disponible, partout en France.">
<script src="https://cdn.paddle.com/paddle/v2/paddle.js"></script>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1a1a2e; }}
  h1 {{ font-size: 28px; }}
  .prix {{ font-size: 22px; font-weight: bold; color: #185FA5; margin: 20px 0; }}
  button {{ background: #185FA5; color: white; border: none; padding: 14px 28px; font-size: 16px; border-radius: 8px; cursor: pointer; }}
  button:hover {{ background: #134876; }}
  footer {{ margin-top: 60px; font-size: 13px; color: #888; }}
  footer a {{ color: #888; }}
</style>
</head>
<body>

<h1>🏠 CROUS Notif</h1>
<p>Reçois une alerte instantanée dès qu'un logement CROUS redevient disponible — partout en France, 18 zones surveillées en continu.</p>

<div class="prix">10€ / mois</div>

<button id="bouton-paiement">S'abonner maintenant</button>

<p id="message-erreur" style="color:#c0392b; display:none;">
  Impossible d'ouvrir le paiement pour le moment. Réessaie dans un instant.
</p>

<footer>
  <a href="/terms">Conditions d'utilisation</a> · <a href="/privacy">Politique de confidentialité</a><br>
  Contact : {CONTACT_EMAIL}
</footer>

<script>
  const params = new URLSearchParams(window.location.search);
  const chatId = params.get('chat_id') || '';

  try {{
    Paddle.Environment.set('{PADDLE_ENVIRONMENT}');
    Paddle.Initialize({{ token: '{PADDLE_CLIENT_TOKEN}' }});
  }} catch (e) {{
    console.error('Paddle init error', e);
  }}

  document.getElementById('bouton-paiement').addEventListener('click', function () {{
    try {{
      Paddle.Checkout.open({{
        items: [{{ priceId: '{PADDLE_PRICE_ID}', quantity: 1 }}],
        customData: {{ telegram_chat_id: chatId }}
      }});
    }} catch (e) {{
      document.getElementById('message-erreur').style.display = 'block';
      console.error('Checkout error', e);
    }}
  }});
</script>

</body>
</html>""", 200


@app.route("/terms")
def terms():
    return """<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>Conditions d'utilisation — CROUS Notif</title></head>
<body style="font-family:-apple-system,sans-serif;max-width:640px;margin:40px auto;padding:0 20px;line-height:1.6;">
<h1>Conditions d'utilisation</h1>
<p>CROUS Notif est un service d'alerte informant les utilisateurs, par message Telegram, de la disponibilité de logements CROUS en France. Ces informations sont issues de l'API publique du site trouverunlogement.lescrous.fr et sont fournies à titre indicatif.</p>
<p>L'abonnement est facturé 10€ par mois, renouvelé automatiquement jusqu'à résiliation. La résiliation peut être demandée à tout moment auprès du support.</p>
<p>CROUS Notif n'est ni affilié, ni partenaire, ni approuvé par le CROUS ou le CNOUS. Le service ne garantit pas l'obtention d'un logement et n'intervient à aucun moment dans le processus de réservation, qui reste entièrement géré par le site officiel du CROUS.</p>
<p>Contact : voir page d'accueil.</p>
</body></html>""", 200


@app.route("/privacy")
def privacy():
    return """<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>Politique de confidentialité — CROUS Notif</title></head>
<body style="font-family:-apple-system,sans-serif;max-width:640px;margin:40px auto;padding:0 20px;line-height:1.6;">
<h1>Politique de confidentialité</h1>
<p>CROUS Notif collecte uniquement les informations nécessaires au fonctionnement du service : identifiant Telegram (chat_id) et statut d'abonnement. Aucune donnée n'est revendue ni partagée avec des tiers, à l'exception du prestataire de paiement (Paddle) nécessaire au traitement de l'abonnement.</p>
<p>Les données de paiement (numéro de carte, etc.) ne sont jamais stockées par CROUS Notif : elles sont traitées directement par Paddle, notre Merchant of Record.</p>
<p>Pour toute demande de suppression de données, contacte-nous via la page d'accueil.</p>
</body></html>""", 200


@app.route("/pricing")
def pricing():
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tarifs — CROUS Notif</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1a1a2e; }}
  .carte {{ border: 1px solid #ddd; border-radius: 12px; padding: 24px; margin-top: 20px; }}
  .prix {{ font-size: 32px; font-weight: bold; color: #185FA5; }}
  a.bouton {{ display: inline-block; background: #185FA5; color: white; text-decoration: none; padding: 14px 28px; border-radius: 8px; margin-top: 16px; }}
  footer {{ margin-top: 60px; font-size: 13px; color: #888; }}
  footer a {{ color: #888; }}
</style>
</head>
<body>

<h1>Tarifs — CROUS Notif</h1>
<p>Un seul abonnement, tout inclus : toute la France, alertes instantanées.</p>

<div class="carte">
  <div class="prix">10€ <span style="font-size:16px;font-weight:normal;">/ mois</span></div>
  <ul>
    <li>18 zones surveillées (13 régions métropolitaines, Corse, DOM-TOM)</li>
    <li>Vérification toutes les 3 minutes</li>
    <li>Alerte instantanée dès qu'un logement se libère</li>
    <li>Résiliable à tout moment</li>
  </ul>
  <a class="bouton" href="/">S'abonner maintenant</a>
</div>

<footer>
  <a href="/terms">Conditions d'utilisation</a> · <a href="/privacy">Politique de confidentialité</a> · <a href="/refund">Remboursement</a><br>
  Contact : {CONTACT_EMAIL}
</footer>

</body>
</html>""", 200


@app.route("/refund")
def refund():
    return """<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><title>Politique de remboursement — CROUS Notif</title></head>
<body style="font-family:-apple-system,sans-serif;max-width:640px;margin:40px auto;padding:0 20px;line-height:1.6;">
<h1>Politique de remboursement</h1>
<p>Si le service ne fonctionne pas comme annoncé au cours des 7 premiers jours suivant ton premier paiement (par exemple : aucune alerte reçue alors que des logements étaient disponibles dans les zones couvertes), tu peux demander un remboursement intégral en nous contactant via la page d'accueil.</p>
<p>Passé ce délai de 7 jours, l'abonnement peut être résilié à tout moment pour arrêter les prélèvements futurs, sans remboursement du mois déjà entamé.</p>
<p>Les demandes de remboursement sont traitées sous 5 jours ouvrés.</p>
</body></html>""", 200


@app.route("/status")
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
    Reçoit les messages envoyés au bot en privé.
    /start renvoie le prix et le lien d'abonnement Tribute — c'est
    Tribute qui gère ensuite l'ajout au canal privé après paiement.
    """

    update = request.get_json(silent=True) or {}
    message = update.get("message", {})
    texte = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not chat_id:
        return "ok", 200

    if texte.startswith("/start"):

        lien_paiement = f"{RENDER_URL}?chat_id={chat_id}"

        reponse = (
            "👋 Bienvenue sur CROUS Notif !\n\n"
            "Une alerte instantanée dès qu'un logement CROUS "
            "redevient disponible, partout en France.\n\n"
            "💳 Accès : 10€/mois\n\n"
            "Abonne-toi ici :\n"
            f"{lien_paiement}"
        )

        try:
            envoyer_message_simple(chat_id, reponse)
        except Exception as erreur:
            print(f"⚠️ Erreur réponse /start : {erreur}")

    return "ok", 200


@app.route("/paddle-webhook", methods=["POST"])
def paddle_webhook():
    """
    Reçoit les notifications de paiement de Paddle.
    - transaction.completed / subscription.created : on invite l'utilisateur au canal
    - subscription.canceled / subscription.past_due : on le retire du canal
    """

    import hashlib
    import hmac as hmac_lib

    corps_brut = request.get_data()
    signature_header = request.headers.get("Paddle-Signature", "")

    print(f"🔍 Paddle-Signature reçu : {signature_header!r}")
    print(f"🔍 PADDLE_WEBHOOK_SECRET configuré : {'oui (' + str(len(PADDLE_WEBHOOK_SECRET)) + ' caractères)' if PADDLE_WEBHOOK_SECRET else 'NON — vide !'}")

    if not signature_header:
        print("❌ Aucun header Paddle-Signature reçu — requête pas envoyée par Paddle, ou proxy qui le filtre.")
        return "missing signature header", 400

    if PADDLE_WEBHOOK_SECRET:
        try:
            parties = {}
            for p in signature_header.split(";"):
                if "=" in p:
                    cle, valeur = p.split("=", 1)
                    parties[cle.strip()] = valeur.strip()

            ts = parties.get("ts", "")
            h1 = parties.get("h1", "")

            if not ts or not h1:
                print(f"❌ ts ou h1 manquant après parsing : parties={parties}")
                return "malformed signature", 400

            payload_signe = f"{ts}:{corps_brut.decode('utf-8')}"
            signature_calculee = hmac_lib.new(
                PADDLE_WEBHOOK_SECRET.encode("utf-8"),
                payload_signe.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            if not hmac_lib.compare_digest(signature_calculee, h1):
                print(f"❌ Signature invalide. Reçu (h1)={h1} | Calculée={signature_calculee}")
                return "invalid signature", 400

            print("✅ Signature Paddle valide.")

        except Exception as erreur:
            print(f"❌ Erreur vérification signature Paddle : {erreur}")
            return "signature error", 400
    else:
        print("⚠️ PADDLE_WEBHOOK_SECRET vide : signature non vérifiée (à corriger avant la prod !).")

    event = request.get_json(silent=True) or {}
    event_type = event.get("event_type", "")
    data = event.get("data", {})

    print(f"📩 Événement Paddle reçu : {event_type}")

    if event_type in ("transaction.completed",):

        custom_data = data.get("custom_data") or {}
        chat_id = custom_data.get("telegram_chat_id")

        if chat_id:
            inviter_au_canal(chat_id)
        else:
            print("⚠️ transaction.completed sans telegram_chat_id dans custom_data.")

    elif event_type in ("subscription.canceled", "subscription.past_due"):

        custom_data = data.get("custom_data") or {}
        chat_id = custom_data.get("telegram_chat_id")

        if chat_id:
            retirer_du_canal(chat_id)

    return "ok", 200


def inviter_au_canal(chat_id):
    """Génère un lien d'invitation à usage unique et l'envoie en DM."""

    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/createChatInviteLink"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": os.getenv("TELEGRAM_CHANNEL_ID"),
                "member_limit": 1,
                "name": f"invite-{chat_id}"
            },
            timeout=15
        )
        response.raise_for_status()
        lien_invitation = response.json()["result"]["invite_link"]

        envoyer_message_simple(
            chat_id,
            "✅ Paiement confirmé !\n\n"
            "Rejoins le canal d'alertes ici (lien à usage unique) :\n"
            f"{lien_invitation}"
        )
        print(f"✅ Invitation envoyée à {chat_id}")

    except Exception as erreur:
        print(f"❌ Erreur invitation canal pour {chat_id} : {erreur}")


def retirer_du_canal(chat_id):
    """Retire un utilisateur du canal (abonnement expiré/annulé)."""

    token = os.getenv("TELEGRAM_TOKEN")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/banChatMember",
            json={"chat_id": channel_id, "user_id": chat_id},
            timeout=15
        )
        requests.post(
            f"https://api.telegram.org/bot{token}/unbanChatMember",
            json={"chat_id": channel_id, "user_id": chat_id},
            timeout=15
        )
        print(f"🗑️ {chat_id} retiré du canal (abonnement terminé)")

    except Exception as erreur:
        print(f"❌ Erreur retrait canal pour {chat_id} : {erreur}")


if __name__ == "__main__":
    threading.Thread(target=boucle_surveillance, daemon=True).start()
    threading.Thread(target=boucle_auto_ping, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
