def detecter_changements(anciens_etats, logements_actuels):
    alertes = []
    nouveaux_etats = anciens_etats.copy()

    for logement in logements_actuels:

        logement_id = str(logement["id"])
        disponible_maintenant = logement["available"]

        ancien = anciens_etats.get(logement_id)

        # Nouveau logement
        if ancien is None:

            if disponible_maintenant:
                alertes.append(logement)

            nouveaux_etats[logement_id] = logement
            continue

        disponible_avant = ancien.get("available", False)

        # Indisponible → disponible
        if not disponible_avant and disponible_maintenant:
            alertes.append(logement)

        # Toujours mettre à jour l'état
        nouveaux_etats[logement_id] = logement

    return alertes, nouveaux_etats