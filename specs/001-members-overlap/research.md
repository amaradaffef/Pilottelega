# Phase 0 — Research: Pilottelega

Aucune zone `NEEDS CLARIFICATION` dans le Technical Context (stack figée par la
constitution v1.0.0). Ce document consolide les décisions et bonnes pratiques.

## D1 — Framework UI : PySide6

- **Decision** : PySide6 (Qt for Python officiel) avec `QTabWidget` + `QTableView`/`QTableWidget`.
- **Rationale** : onglets natifs (un par groupe + Analyse), tables performantes pour
  des milliers de lignes, licence LGPL compatible projet libre, widget standard mature.
- **Alternatives** : Tkinter (tables faibles, peu ergonomique), PyQt6 (licence GPL/commerciale
  plus contraignante), CustomTkinter (pas de table performante). Rejetées.

## D2 — Accès Telegram : Telethon

- **Decision** : Telethon (client MTProto) avec `iter_participants` / `get_participants`.
- **Rationale** : API utilisateur officielle, gère le login (code + 2FA), la session
  persistée, et l'itération sur les membres ; déjà retenu dans la roadmap. Licence MIT.
- **Alternatives** : Pyrogram (équivalent, mais Telethon déjà maîtrisé), Bot API (ne permet
  pas de lister les membres arbitraires). Rejetées.

## D3 — Pont asynchrone : qasync

- **Decision** : qasync, boucle asyncio intégrée à la boucle d'événements Qt ; `main.py`
  bootstrappe `QEventLoop(app)` et `loop.run_forever()`.
- **Rationale** : Telethon est `async` ; sans pont, l'UI gèle pendant login/fetch (Principe III).
  qasync permet d'`await` des coroutines depuis les slots Qt. À câbler **dès le jalon 1**.
- **Alternatives** : `QThread` + exécution d'une boucle asyncio dans le thread (plus complexe,
  marshalling manuel des signaux) ; `threading` brut (risqué avec Telethon). Rejetées.
- **Bonnes pratiques** : démarrer les coroutines via `asyncio.ensure_future` depuis les slots ;
  ne jamais bloquer le thread UI ; afficher un indicateur de progression pendant les `await`.

## D4 — Stockage local des identifiants & session

- **Decision** : config (`api_id`, `api_hash`, `phone`) + fichier session Telethon stockés
  sous `%APPDATA%/Pilottelega/`. Aucun secret dans l'`.exe`.
- **Rationale** : Principe II (confidentialité, jamais embarqué). `%APPDATA%` est le standard
  Windows par utilisateur. Le fichier session Telethon (`.session`) suffit à éviter une
  reconnexion (FR-003).
- **Bonnes pratiques** : `.session` ignoré par git (déjà dans `.gitignore`). Chiffrement du
  stockage = durcissement **post-MVP** (hors périmètre, Principe IV).
- **Alternatives** : registre Windows (moins portable), keyring OS (ajout de dépendance,
  post-MVP). Rejetées pour le MVP.

## D5 — Identité stable d'un membre (clé de recoupement)

- **Decision** : clé = `user_id` Telegram (entier stable). Le `@username` est optionnel et
  sert uniquement à l'affichage (avec repli sur nom affiché puis `id`).
- **Rationale** : FR-012 exige une identité stable indépendante du `@username` (qui peut être
  absent ou changer). `user_id` est immuable.
- **Alternatives** : `@username` (instable/absent), nom affiché (non unique). Rejetées comme clé.

## D6 — Détection du statut d'accès par groupe

- **Decision** : enum `AccessStatus` = `FULL` / `PARTIAL_HIDDEN` / `ADMIN_REQUIRED` / `ERROR`.
  Déduit du résultat Telethon : succès complet → FULL ; `ChatAdminRequiredError` →
  ADMIN_REQUIRED ; liste vide/tronquée sur groupe à membres masqués → PARTIAL_HIDDEN ;
  autre exception → ERROR (message conservé).
- **Rationale** : FR-010/011 — afficher la réalité de l'accès sans contourner. Mapping
  d'exceptions explicite et testable (via mocks en integration).
- **Alternatives** : tenter des contournements (interdit, Principe II). Rejeté.

## D7 — Normalisation des liens de groupes

- **Decision** : `link_parser` accepte `@nom`, `https://t.me/nom`, `t.me/nom`, `t.me/+invite`
  (lien d'invitation), et identifiant numérique ; produit une cible normalisée + signale les
  entrées invalides sans interrompre le lot.
- **Rationale** : FR-006/007. Fonction pure → testable unitairement sans réseau.
- **Bonnes pratiques** : strip des espaces, ignorer lignes vides, dédupliquer (FR-015).

## D8 — Réactivité & gros volumes

- **Decision** : itération asynchrone des membres avec mise à jour de progression ; traitement
  en mémoire ; pas de pagination persistée.
- **Rationale** : Principe IV (simplicité) + III (réactivité). Quelques groupes/milliers de
  membres tiennent en mémoire. SC-005.
- **Alternatives** : streaming vers DB (post-MVP). Rejeté pour le MVP.

## D9 — Qualité & CI

- **Decision** : Black (format), Ruff (lint), type hints, pytest ; GitHub Actions exécutant
  `ruff check`, `black --check`, `pytest` à chaque push/PR.
- **Rationale** : standards de code du projet (CLAUDE.md) + Principe V. Le merge auto ne
  passe que si la CI est verte.
- **Alternatives** : Pylint (plus lent), flake8+isort (Ruff couvre les deux). Rejetées.

## D10 — Packaging Windows

- **Decision** : PyInstaller → `.exe` autonome (jalon 5), après validation de la logique via
  `python -m pilottelega`.
- **Rationale** : roadmap §6 ; emballage en dernier. Aucun secret embarqué (D4).
- **Alternatives** : cx_Freeze, Nuitka (plus complexes). Rejetées pour le MVP.
