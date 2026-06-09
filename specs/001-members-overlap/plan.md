# Implementation Plan: Pilottelega — Membres & recoupement de groupes Telegram

**Branch**: `001-members-overlap` | **Date**: 2026-06-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-members-overlap/spec.md`

## Summary

Application desktop Windows qui connecte l'utilisateur à son compte Telegram (onboarding
avec identifiants personnels stockés localement), récupère les membres de groupes saisis
par lien, affiche un onglet par groupe avec son statut d'accès, puis croise les listes
pour distinguer les membres présents dans un seul groupe de ceux présents dans plusieurs.

**Approche technique** : interface PySide6 (onglets `QTabWidget`, tables), accès Telegram
via Telethon, pont **qasync** pour exécuter les appels réseau asynchrones sans geler l'UI.
Logique métier (parsing de liens, calcul de recoupement) **isolée de l'UI** et testée avec
pytest. Données **en mémoire** (pas de base de données pour le MVP). Distribution en `.exe`
autonome via PyInstaller.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: PySide6 (UI), Telethon (API Telegram), qasync (pont asyncio/Qt)

**Storage**: En mémoire pour les données métier ; config + session Telethon stockées en
fichiers locaux sous `%APPDATA%/Pilottelega/` (jamais embarquées dans l'`.exe`)

**Testing**: pytest (logique métier isolée) ; Ruff + Black --check en CI

**Target Platform**: Windows 10/11 (desktop), application mono-utilisateur locale

**Project Type**: Desktop application (UI + logique + accès externe), structure type MVC

**Performance Goals**: UI réactive en continu (aucun gel perceptible > ~100 ms) pendant les
appels réseau ; récupération de quelques groupes (jusqu'à ~10) par session

**Constraints**: Stockage local uniquement, aucun secret embarqué/transmis ; lecture seule
sur Telegram ; respect des restrictions d'accès (pas de contournement) ; offline impossible
(dépend du réseau Telegram) mais l'app ne plante pas hors connexion

**Scale/Scope**: Quelques groupes simultanés, milliers de membres en mémoire ; ~4 écrans
(onboarding, écran principal/saisie, onglets de groupe, onglet Analyse)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe (constitution v1.0.0) | Gate | Statut |
|---|---|---|
| I. Open Source & Gratuit (MIT) | `LICENSE` MIT présent, aucune dépendance non libre | ✅ PASS — LICENSE MIT en place ; PySide6 (LGPL/commercial), Telethon (MIT), qasync (BSD) compatibles usage libre |
| II. Conformité, accès légitime & confidentialité | Statut d'accès affiché par groupe ; identifiants/session en local ; aucun contournement | ✅ PASS — design affiche `AccessStatus`, stockage `%APPDATA%`, lecture seule |
| III. UI réactive non bloquante | qasync câblé dès le 1er appel réseau (onboarding) | ✅ PASS — qasync au bootstrap, services réseau `async` |
| IV. Simplicité MVP-first (YAGNI) | En mémoire, pas de DB ; pas de fonctions post-MVP | ✅ PASS — aucune persistance des membres, pas de SQLite/planif/multi-comptes |
| V. Qualité & testabilité | Logique métier isolée de l'UI + tests ; lançable via `python` | ✅ PASS — package `core/` sans dépendance Qt, testé pytest, CI Ruff/Black/pytest |

**Résultat** : tous les gates passent. Aucune violation → section *Complexity Tracking* vide.

## Project Structure

### Documentation (this feature)

```text
specs/001-members-overlap/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (interfaces internes des services + UI)
│   ├── telegram-service.md
│   ├── analysis-service.md
│   └── ui-screens.md
├── checklists/
│   └── requirements.md  # déjà généré par /speckit-specify
└── tasks.md             # Phase 2 output (/speckit-tasks — PAS créé ici)
```

### Source Code (repository root)

Structure type **MVC** : `core/` (Model + logique, sans Qt, testable) ; `ui/` (View +
Controller PySide6) ; `app/` (assemblage, config, bootstrap qasync).

```text
pilottelega/
├── __init__.py
├── main.py                    # point d'entrée : bootstrap qasync + QApplication, routage onboarding/main
├── app/
│   ├── __init__.py
│   ├── paths.py               # résolution des chemins %APPDATA%/Pilottelega
│   ├── settings.py            # lecture/écriture config locale (api_id/api_hash/phone)
│   └── logging_conf.py        # configuration du module logging
├── core/                      # MODEL + logique métier — AUCUN import Qt, 100% testable
│   ├── __init__.py
│   ├── models.py              # Member, TargetGroup, AccessStatus, AnalysisResult (dataclasses)
│   ├── link_parser.py         # normalisation des liens de groupes (FR-006/007)
│   ├── analysis.py            # calcul des recoupements uniques vs multi-groupes (FR-012/013/014)
│   └── telegram_service.py    # façade async Telethon : login, fetch membres, statut d'accès
├── ui/                        # VIEW + CONTROLLER PySide6
│   ├── __init__.py
│   ├── onboarding.py          # écran 1er lancement (saisie credentials, code, 2FA)
│   ├── main_window.py         # fenêtre principale + QTabWidget
│   ├── group_tab.py           # onglet par groupe (table membres + statut)
│   └── analysis_tab.py        # onglet Analyse (uniques / multi-groupes)
└── resources/                 # icônes, textes onboarding (optionnel)

tests/
├── unit/                      # link_parser, analysis, models (sans réseau ni Qt)
│   ├── test_link_parser.py
│   └── test_analysis.py
└── integration/               # telegram_service avec mocks Telethon
    └── test_telegram_service.py

.github/workflows/ci.yml       # Ruff + Black --check + pytest
pyproject.toml                 # deps + config Black/Ruff/pytest
requirements.txt
README.md
pilottelega.spec               # config PyInstaller (jalon 5) — généré plus tard
```

**Structure Decision** : application desktop à projet unique, découpée en trois couches —
`core/` (modèle + logique pure, cible des tests unitaires), `ui/` (PySide6), `app/`
(config/bootstrap). Cette séparation matérialise les principes V (testabilité) et III
(le `core.telegram_service` expose des coroutines `async` que l'UI consomme via qasync).

## Complexity Tracking

> Aucune violation de la Constitution Check — section vide.
