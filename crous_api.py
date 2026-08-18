import time

import requests


URL = "https://trouverunlogement.lescrous.fr/api/fr/search/47"


def rechercher_logements(location, max_pages=60, timeout_global=90):
    """
    max_pages : nombre maximum de pages récupérées pour une zone.
    timeout_global : durée maximale (en secondes) passée sur une zone
                      avant d'arrêter la pagination, même si l'API
                      indique qu'il reste des résultats.

    Ces deux garde-fous existent car certaines zones (ex : régions
    entières comme l'Ile-de-France) peuvent contenir des milliers de
    résultats. Sans limite, la pagination peut prendre plusieurs
    dizaines de minutes et bloquer tout le cycle de vérification.
    Si la limite est atteinte, on retourne ce qui a déjà été récupéré
    au lieu de tout perdre.
    """

    logements = []

    page = 1
    page_size = 24

    debut = time.monotonic()

    while True:

        if page > max_pages:
            print(
                f"⚠️ Limite de {max_pages} pages atteinte pour cette "
                f"zone : arrêt anticipé ({len(logements)} logement(s) récupéré(s))."
            )
            break

        if time.monotonic() - debut > timeout_global:
            print(
                f"⚠️ Timeout de {timeout_global}s atteint pour cette "
                f"zone : arrêt anticipé ({len(logements)} logement(s) récupéré(s))."
            )
            break

        payload = {
            "idTool": 47,
            "need_aggregation": True,
            "page": page,
            "pageSize": page_size,
            "sector": None,
            "occupationModes": [],
            "adaptedPmr": False,
            "area": {
                "min": 0
            },
            "equipment": [],
            "location": location,
            "precision": 6,
            "price": {
                "max": 10000000
            },
            "residence": None,
            "toolMechanism": "residual"
        }

        # =========================
        # REQUÊTE API
        # =========================

        response = requests.post(
            URL,
            json=payload,
            timeout=20
        )

        # Erreur HTTP
        response.raise_for_status()

        # =========================
        # JSON
        # =========================

        try:
            data = response.json()

        except ValueError as erreur:

            raise RuntimeError(
                "Réponse CROUS non valide : "
                "ce n'est pas du JSON."
            ) from erreur

        # =========================
        # VALIDATION
        # =========================

        if "results" not in data:

            raise RuntimeError(
                "Réponse CROUS invalide : "
                "'results' absent."
            )

        results = data["results"]

        if "items" not in results:

            raise RuntimeError(
                "Réponse CROUS invalide : "
                "'items' absent."
            )

        if "total" not in results:

            raise RuntimeError(
                "Réponse CROUS invalide : "
                "'total' absent."
            )

        items = results["items"]

        total = results["total"]["value"]

        # =========================
        # TRAITEMENT
        # =========================

        print(
            f"Page {page} : "
            f"{len(items)} logement(s)"
        )

        for item in items:

            occupation_modes = item.get(
                "occupationModes",
                []
            )

            if occupation_modes:

                loyer = (
                    occupation_modes[0]
                    ["rent"]["min"]
                    / 100
                )

            else:

                loyer = None

            residence = item.get(
                "residence",
                {}
            )

            entity = residence.get(
                "entity",
                {}
            )

            area = item.get(
                "area",
                {}
            )

            logement = {
                "id": item["id"],

                "residence": residence.get(
                    "label",
                    "Inconnue"
                ),

                "ville": entity.get(
                    "name",
                    "Inconnue"
                ),

                "adresse": residence.get(
                    "address",
                    "Adresse inconnue"
                ),

                "type": item.get(
                    "label",
                    "Type inconnu"
                ),

                "surface": area.get(
                    "min",
                    0
                ),

                "loyer": loyer,

                "available": item.get(
                    "available",
                    False
                )
            }

            logements.append(logement)

        # =========================
        # FIN DE LA PAGINATION
        # =========================

        if not items:
            break

        if len(logements) >= total:
            break

        page += 1

    return logements