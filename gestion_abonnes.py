"""
Script à usage manuel pour l'administrateur (toi).
S'exécute depuis ton PC (nécessite Python + les dépendances installées).

Avant utilisation, crée un fichier .env local (à côté de ce script) avec :
    GITHUB_TOKEN=ton_personal_access_token_github
    GITHUB_REPO=Jugurtha-0/crous-bot

Utilisation :
    python gestion_abonnes.py ajouter 5179454011 "Prénom Nom"
    python gestion_abonnes.py retirer 5179454011
    python gestion_abonnes.py lister

Chaque commande lit/écrit directement abonnes.json dans le dépôt
GitHub — le bot sur Render lira automatiquement la version à jour au
prochain message ou à la prochaine alerte, sans qu'il y ait besoin de
redéployer quoi que ce soit.
"""

import sys

from dotenv import load_dotenv

load_dotenv()

from abonnes import ajouter_abonne, retirer_abonne, charger_abonnes


def main():

    if len(sys.argv) < 2:
        print(__doc__)
        return

    commande = sys.argv[1]

    if commande == "ajouter":
        if len(sys.argv) < 3:
            print("Usage : python gestion_abonnes.py ajouter <chat_id> [nom]")
            return
        chat_id = int(sys.argv[2])
        nom = sys.argv[3] if len(sys.argv) > 3 else ""
        ajouter_abonne(chat_id, nom)

    elif commande == "retirer":
        if len(sys.argv) < 3:
            print("Usage : python gestion_abonnes.py retirer <chat_id>")
            return
        chat_id = int(sys.argv[2])
        retirer_abonne(chat_id)

    elif commande == "lister":
        abonnes = charger_abonnes()
        if not abonnes:
            print("Aucun abonné pour l'instant.")
        else:
            print(f"{len(abonnes)} abonné(s) :")
            for a in abonnes:
                print(f"  - {a['chat_id']}  {a.get('nom', '')}")

    else:
        print(f"Commande inconnue : {commande}")
        print(__doc__)


if __name__ == "__main__":
    main()
