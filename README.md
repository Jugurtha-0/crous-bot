# Bot de surveillance des logements CROUS

Surveille toute la France (13 régions métropolitaines + Corse + DOM-TOM) et
poste une alerte dans un canal Telegram privé dès qu'un logement CROUS
redevient disponible.

## Monétisation : Tribute + canal privé

L'accès au canal d'alertes est payant (10€/mois), géré automatiquement par
**Tribute** (bot Telegram) :

- Tribute gère les paiements, les renouvellements automatiques, et
  ajoute/retire les membres du canal selon leur abonnement.
- Le bot (`server.py`) n'a plus besoin de connaître la liste des abonnés :
  il poste simplement les alertes dans le canal, Tribute s'occupe du reste.
- `/start` en message privé au bot renvoie le lien de paiement Tribute.

### Variables d'environnement nécessaires

- `TELEGRAM_TOKEN` — token du bot (@BotFather)
- `TELEGRAM_CHANNEL_ID` — identifiant du canal privé (ex : `-1004342850854`)
- `LIEN_PAIEMENT_TRIBUTE` — le lien d'abonnement généré par @Tribute
  (ex : `https://t.me/tribute/app?startapp=xxxxx`)

## Hébergement gratuit (sans carte bancaire), 24h/24 — Render

Sur le plan gratuit de Render, seul le type **Web Service** est disponible
sans carte bancaire (les *background workers* et *cron jobs* sont payants
depuis 2026). `server.py` est un petit serveur Flask qui :

1. lance la surveillance CROUS dans un thread en arrière-plan, toutes les
   **3 minutes** ;
2. s'auto-ping toutes les 10 minutes via sa propre URL publique
   (`RENDER_EXTERNAL_URL`, fournie automatiquement par Render), pour ne
   jamais dépasser le seuil d'inactivité de 15 minutes qui met le service
   en veille.

Grâce à ça, **pas besoin de service externe** (type cron-job.org) pour le
garder éveillé — le service se maintient lui-même.

### Étapes

1. Pousse ce dossier sur GitHub.
2. Sur [render.com](https://render.com), crée un compte (aucune carte
   requise pour le tier gratuit), puis **New → Web Service**, connecte ton
   dépôt. Render lit `render.yaml` automatiquement et propose le plan Free.
3. Renseigne `TELEGRAM_TOKEN` et `TELEGRAM_CHAT_ID` dans l'onglet
   *Environment* du service.
4. Déploie. Render te donne une URL du style
   `https://crous-bot.onrender.com` — le service s'auto-ping ensuite tout
   seul, tu n'as rien d'autre à configurer.

### ⚠️ Limites à connaître

- **750 heures gratuites/mois** : un service qui tourne en continu consomme
  ~744h/mois (31 jours × 24h) — tu es tout juste dans la limite, mais ça
  passe.
- **Disque éphémère** : si Render redémarre le service (ça arrive de temps
  en temps sur le tier gratuit, indépendamment de l'inactivité), le fichier
  `etat_logements.json` repart de zéro. Le bot peut alors renvoyer une
  alerte pour un logement déjà vu — sans gravité, juste un doublon
  occasionnel.
- **Auto-ping = un seul point de défaillance** : si le thread d'auto-ping
  plante silencieusement (rare, mais possible), plus rien ne l'empêche de
  s'endormir. Si tu veux une garantie supplémentaire, ajoute *en plus* un
  ping externe gratuit via [cron-job.org](https://cron-job.org) vers ton
  URL Render toutes les 10 min — les deux mécanismes peuvent cohabiter
  sans problème.

### Fichiers utilisés par cette méthode

- `server.py` — serveur Flask + boucle de surveillance + auto-ping.
- `render.yaml` — configuration Render (infra as code).
- `zone.py`, `crous_api.py`, `etat_logements.py`, `detecteur.py`,
  `telegram.py` — logique métier du bot (inchangée).

## Alternative : GitHub Actions

Moins adapté ici, car limité à une vérification toutes les 5 minutes
minimum (non garanties), contre 3 min fixes avec la méthode Render
ci-dessus. Utile seulement si tu ne veux pas garder un service tournant en
continu.

### Étapes

1. Crée un dépôt GitHub **public** (les dépôts publics ont des minutes
   Actions illimitées ; un dépôt privé a un quota mensuel gratuit limité).
2. Mets-y tous les fichiers de ce dossier (structure telle quelle, y
   compris `.github/workflows/crous.yml`).
3. Dans le dépôt : **Settings → Secrets and variables → Actions → New
   repository secret**, ajoute :
   - `TELEGRAM_TOKEN` → le token de ton bot (via @BotFather)
   - `TELEGRAM_CHAT_ID` → ton chat id (récupérable avec `get_chat_id.py`)
4. Dans **Settings → Actions → General → Workflow permissions**, coche
   *"Read and write permissions"* (sinon le job ne pourra pas sauvegarder
   `etat_logements.json`).
5. Va dans l'onglet **Actions** du dépôt, ouvre "CROUS Watcher", clique
   **"Run workflow"** pour tester une première fois.
6. C'est tout : ensuite ça tourne tout seul toutes les 5 minutes.

### ⚠️ Point important

GitHub désactive automatiquement un workflow planifié (`schedule`) si le
dépôt reste 60 jours sans **aucune** activité. Comme ce workflow commit
lui-même `etat_logements.json` à chaque run, ça compte comme de
l'activité et le problème ne se pose pas tant qu'il tourne — mais si tu le
mets en pause longtemps, il faudra le relancer manuellement une fois
(bouton "Run workflow").

### Fichiers utilisés par cette méthode

- `surveillance.py` — le script exécuté par le workflow (un seul passage,
  puis il s'arrête — c'est GitHub qui le relance toutes les 5 min).
- `bot_crous.py` — variante "boucle infinie" (`while True` + `sleep`),
  utile si un jour tu héberges ça sur un vrai serveur/VPS à toi ; **ne
  sert pas** avec GitHub Actions (un job Actions a une durée maximale et
  serait tué).
- `.github/workflows/crous.yml` — la planification GitHub Actions.

## Vérifier / ajuster les zones

Les rectangles de `zone.py` sont volontairement larges pour ne rater
aucune résidence. Si l'API renvoie une erreur ou un timeout sur une
zone précise, réduis-la (par exemple en la coupant en deux zones plus
petites).
