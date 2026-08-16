from etat_logements import charger_etats, sauvegarder_etats


etats = charger_etats()

print("États actuels :", etats)


etats["1224"] = {
    "available": True,
    "residence": "BAZEILLES",
    "type": "T1Bis",
    "loyer": 426.0
}

sauvegarder_etats(etats)

print("État sauvegardé.")
