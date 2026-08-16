from zone import ZONES
from crous_api import rechercher_logements
from etat_logements import charger_etats, sauvegarder_etats
from detecteur import detecter_changements
from telegram import envoyer_telegram

anciens_etats = charger_etats()

tous_les_logements = []


for nom_zone, location in ZONES.items():

    print(f"\n🔍 Recherche : {nom_zone}")

    try:
        logements = rechercher_logements(location)

        print(
            f"   {len(logements)} logement(s) trouvé(s)"
        )

        tous_les_logements.extend(logements)

    except Exception as erreur:

        print(
            f"❌ Erreur pour {nom_zone} : {erreur}"
        )


alertes, nouveaux_etats = detecter_changements(
    anciens_etats,
    tous_les_logements
)


sauvegarder_etats(nouveaux_etats)


print("\n==============================")
print("RÉSULTAT")
print("==============================")

if alertes:

    print(
        f"🚨 {len(alertes)} nouvelle(s) disponibilité(s)"
    )

    for logement in alertes:

        print(
            f"\n🏠 {logement['residence']}"
            f"\n📍 {logement['ville']}"
            f"\n🛏️ {logement['type']}"
            f"\n💰 {logement['loyer']} €"
            f"\n📐 {logement['surface']} m²"
        )
        envoyer_telegram(logement)

else:

    print("Aucune nouvelle disponibilité.")