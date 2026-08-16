# zone.py
#
# Chaque zone est un rectangle géographique défini par 2 points
# (coin nord-ouest / coin sud-est approximatifs). L'API CROUS
# renvoie tous les logements dont les coordonnées tombent dans
# ce rectangle -> pas besoin de connaître chaque résidence,
# il suffit que le rectangle couvre toute la région.
#
# Ces 18 zones couvrent : les 13 régions métropolitaines,
# la Corse, et les 5 DOM (Guadeloupe, Martinique, Guyane,
# La Réunion, Mayotte).
#
# ⚠️ Les rectangles sont volontairement larges pour ne rater
# aucune résidence. Si tu observes des zones qui ne renvoient
# rien ou des erreurs sur une zone précise, réduis-la légèrement.

ZONES = {

    "Ile-de-France": [
        {"lon": 1.40, "lat": 49.30},
        {"lon": 3.60, "lat": 48.10}
    ],

    "Hauts-de-France": [
        {"lon": 1.30, "lat": 51.10},
        {"lon": 4.30, "lat": 49.30}
    ],

    "Normandie": [
        {"lon": -1.95, "lat": 50.10},
        {"lon": 1.85, "lat": 48.20}
    ],

    "Bretagne": [
        {"lon": -5.20, "lat": 48.90},
        {"lon": -1.00, "lat": 47.20}
    ],

    "Pays-de-la-Loire": [
        {"lon": -2.55, "lat": 48.60},
        {"lon": 0.95, "lat": 46.25}
    ],

    "Centre-Val-de-Loire": [
        {"lon": 0.00, "lat": 48.75},
        {"lon": 3.15, "lat": 46.30}
    ],

    "Grand-Est": [
        {"lon": 3.35, "lat": 50.20},
        {"lon": 8.25, "lat": 47.40}
    ],

    "Bourgogne-Franche-Comte": [
        {"lon": 2.80, "lat": 48.40},
        {"lon": 7.20, "lat": 46.10}
    ],

    "Nouvelle-Aquitaine": [
        {"lon": -1.85, "lat": 46.95},
        {"lon": 2.65, "lat": 42.75}
    ],

    "Occitanie": [
        {"lon": -0.35, "lat": 45.05},
        {"lon": 4.95, "lat": 42.30}
    ],

    "Auvergne-Rhone-Alpes": [
        {"lon": 2.00, "lat": 46.85},
        {"lon": 7.20, "lat": 44.05}
    ],

    "Provence-Alpes-Cote-d-Azur": [
        {"lon": 4.20, "lat": 45.15},
        {"lon": 7.75, "lat": 42.90}
    ],

    "Corse": [
        {"lon": 8.50, "lat": 43.10},
        {"lon": 9.60, "lat": 41.30}
    ],

    # -------- DOM-TOM --------

    "Guadeloupe": [
        {"lon": -61.90, "lat": 16.60},
        {"lon": -61.00, "lat": 15.80}
    ],

    "Martinique": [
        {"lon": -61.30, "lat": 14.90},
        {"lon": -60.80, "lat": 14.35}
    ],

    "Guyane": [
        {"lon": -54.60, "lat": 5.80},
        {"lon": -51.60, "lat": 2.10}
    ],

    "La-Reunion": [
        {"lon": 55.20, "lat": -20.85},
        {"lon": 55.85, "lat": -21.40}
    ],

    "Mayotte": [
        {"lon": 45.00, "lat": -12.60},
        {"lon": 45.30, "lat": -13.00}
    ]

}
