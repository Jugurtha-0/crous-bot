import time
from datetime import datetime

from zone import ZONES
from crous_api import rechercher_logements
from etat_logements import charger_etats, sauvegarder_etats
from detecteur import detecter_changements
from telegram import envoyer_telegram


INTERVALLE = 3 * 60  # 3 minutes


def effectuer_verification():

    print("\n" + "=" * 50)
    print(
        "🔍 Vérification :",
        datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )
    print("=" * 50)

    anciens_etats = charger_etats()

    tous_les_logements = []

    zones_reussies = 0
    zones_echouees = 0

    for nom_zone, location in ZONES.items():

        print(f"\n🔎 {nom_zone}")

        try:
            logements = rechercher_logements(location)

            print(
                f"   ✅ {len(logements)} logement(s) trouvé(s)"
            )

            tous_les_logements.extend(logements)

            zones_reussies += 1

        except Exception as erreur:

            zones_echouees += 1

            print(
                f"   ❌ Erreur API pour {nom_zone}"
            )

            print(
                f"   Détail : {erreur}"
            )

            # IMPORTANT :
            # On ne modifie pas les états de cette zone.
            continue

    print("\n" + "-" * 50)

    print(
        f"Zones réussies : {zones_reussies}"
    )

    print(
        f"Zones échouées : {zones_echouees}"
    )

    # Si toutes les zones ont échoué,
    # surtout ne rien modifier.
    if zones_reussies == 0:

        print(
            "\n⚠️ Aucune zone n'a répondu correctement."
        )

        print(
            "⚠️ États précédents conservés."
        )

        return

    alertes, nouveaux_etats = detecter_changements(
        anciens_etats,
        tous_les_logements
    )

    sauvegarder_etats(nouveaux_etats)

    if alertes:

        print(
            f"\n🚨 {len(alertes)} nouvelle(s) "
            f"disponibilité(s) !"
        )

        for logement in alertes:

            print(
                f"\n🏠 {logement['residence']}"
                f"\n📍 {logement['ville']}"
                f"\n🛏️ {logement['type']}"
                f"\n💰 {logement['loyer']} €"
                f"\n📐 {logement['surface']} m²"
            )

            try:

                envoyer_telegram(logement)

                print("📱 Telegram envoyé")

            except Exception as erreur:

                print(
                    f"❌ Erreur Telegram : {erreur}"
                )

    else:

        print(
            "\n✅ Aucune nouvelle disponibilité."
        )


while True:

    try:
        effectuer_verification()

    except Exception as erreur:

        print(
            f"\n❌ Erreur générale : {erreur}"
        )

    print("\n⏳ Prochaine vérification dans 3 minutes...")

    time.sleep(INTERVALLE)