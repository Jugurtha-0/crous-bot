from detecteur import detecter_changements


anciens_etats = {
    "100": {
        "id": 100,
        "available": False,
        "residence": "Test",
        "type": "T1",
        "loyer": 300
    }
}


logements_actuels = [
    {
        "id": 100,
        "available": True,
        "residence": "Test",
        "type": "T1",
        "loyer": 300
    }
]


alertes, nouveaux_etats = detecter_changements(
    anciens_etats,
    logements_actuels
)


print("Nombre d'alertes :", len(alertes))

for logement in alertes:
    print(
        "🚨 ALERTE :",
        logement["residence"],
        logement["type"],
        logement["loyer"],
        "€"
    )