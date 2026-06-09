---

description: "Task list for Pilottelega — Membres & recoupement de groupes Telegram"
---

# Tasks: Pilottelega — Membres & recoupement de groupes Telegram

**Input**: Design documents from `specs/001-members-overlap/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: INCLUS — la constitution (Principe V) et les standards de code (CLAUDE.md)
imposent pytest + CI sur la logique métier. Les tests de `core/` sont écrits avant
l'implémentation correspondante (Red → Green).

**Organization**: tâches groupées par user story pour une livraison MVP incrémentale.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallélisable (fichiers différents, aucune dépendance bloquante)
- **[Story]**: user story rattachée (US1, US2, US3)
- Chemins de fichiers exacts inclus. Package racine : `pilottelega/` ; tests : `tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: initialisation du projet et de l'outillage qualité.

- [ ] T001 Créer la structure du projet (packages + `__init__.py`) : `pilottelega/{app,core,ui}/`, `tests/{unit,integration}/`, dossier `resources/` — conforme à plan.md
- [ ] T002 [P] Créer `pyproject.toml` : dépendances (PySide6, Telethon, qasync) + dev (pytest, ruff, black) + config Black/Ruff/pytest + type hints
- [ ] T003 [P] Créer `requirements.txt` (runtime + dev) cohérent avec `pyproject.toml`
- [ ] T004 [P] Créer le workflow CI `.github/workflows/ci.yml` : `ruff check .`, `black --check .`, `pytest` à chaque push/PR
- [ ] T005 [P] Créer `README.md` (description, prérequis, install dev, `python -m pilottelega`, licence MIT, mention conformité Telegram/RGPD)

**Checkpoint**: projet lançable et outillage qualité en place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: socle partagé par toutes les user stories. ⚠️ AUCUNE user story ne démarre avant.

- [ ] T006 [P] Créer le modèle de données dans `pilottelega/core/models.py` : enum `AccessStatus` (FULL/PARTIAL_HIDDEN/ADMIN_REQUIRED/ERROR), dataclasses `Member` (égalité/hash sur `user_id`), `TargetGroup`, `AnalysisResult` — conforme à data-model.md. Aucun import Qt.
- [ ] T007 [P] Créer `pilottelega/app/paths.py` : résolution de `%APPDATA%/Pilottelega/` (config + chemin session)
- [ ] T008 [P] Créer `pilottelega/app/logging_conf.py` : configuration du module `logging` (pas de `print`), niveau + format, jamais de secret loggé
- [ ] T009 Créer `pilottelega/app/settings.py` : lecture/écriture locale de `api_id`/`api_hash`/`phone` (dépend de T007)
- [ ] T010 Créer `pilottelega/main.py` : bootstrap **qasync** (`QApplication` + `QEventLoop`, `run_forever`) et squelette de routage au démarrage (dépend de T006, T009). Le câblage qasync est posé ici (Principe III, dès le 1er appel réseau).

**Checkpoint**: socle prêt — les user stories peuvent commencer.

---

## Phase 3: User Story 1 - Premier lancement : connexion sécurisée (Priority: P1) 🎯 MVP

**Goal**: relier l'app au compte Telegram (onboarding + login code/2FA), session sauvegardée
localement, sans ressaisie au 2ᵉ lancement.

**Independent Test**: sur profil vierge, compléter l'onboarding jusqu'à connexion réussie ;
fermer/rouvrir → l'écran principal s'ouvre sans ressaisie.

### Tests for User Story 1 ⚠️ (écrire d'abord, doivent échouer)

- [ ] T011 [P] [US1] Test d'intégration `tests/integration/test_telegram_service_login.py` (mocks Telethon) : `is_authorized`, `start_login`, `submit_code` → CONNECTED / PASSWORD_REQUIRED, `submit_password`

### Implementation for User Story 1

- [ ] T012 [US1] Implémenter le cycle de login dans `pilottelega/core/telegram_service.py` : `TelegramService(api_id, api_hash, session_path)`, `is_authorized`, `start_login`, `submit_code`, `submit_password`, persistance locale de la session — façade `async`, aucun import Qt (contracts/telegram-service.md)
- [ ] T013 [US1] Créer l'écran d'onboarding `pilottelega/ui/onboarding.py` : explication + lien cliquable vers la page de génération, champs `api_id`/`api_hash`/téléphone, code, mot de passe 2FA ; appels `await` via qasync avec indicateur de progression (contracts/ui-screens.md)
- [ ] T014 [US1] Compléter le routage dans `pilottelega/main.py` : si `is_authorized()` → fenêtre principale, sinon onboarding (FR-005) (dépend de T010, T012, T013)
- [ ] T015 [US1] Gestion d'erreurs + `logging` du flux de login : messages clairs, saisie corrigeable, pas de plantage, détection session expirée → retour onboarding (FR-017)

**Checkpoint**: US1 fonctionnelle et testable seule (connexion + persistance de session).

---

## Phase 4: User Story 2 - Saisir des groupes et récupérer leurs membres (Priority: P2)

**Goal**: coller des liens de groupes, récupérer les membres, un onglet par groupe avec son
statut d'accès.

**Independent Test**: coller plusieurs liens accessibles, lancer la récupération → un onglet par
groupe avec membres + statut d'accès cohérent ; une ligne invalide n'interrompt pas le lot.

### Tests for User Story 2 ⚠️

- [ ] T016 [P] [US2] Test unitaire `tests/unit/test_link_parser.py` : `normalize_link` (formes valides/invalides), `parse_links` (déduplication, lignes vides, invalides collectées)
- [ ] T017 [P] [US2] Test d'intégration `tests/integration/test_telegram_service_fetch.py` (mocks Telethon) : `fetch_group` produit chaque `AccessStatus` (FULL / PARTIAL_HIDDEN / ADMIN_REQUIRED / ERROR)

### Implementation for User Story 2

- [ ] T018 [P] [US2] Créer `pilottelega/core/link_parser.py` : `normalize_link`, `parse_links` — fonctions pures (FR-006/007/015) (contracts/analysis-service.md)
- [ ] T019 [US2] Étendre `pilottelega/core/telegram_service.py` avec `fetch_group(identifier)` : itération des membres + mapping d'exceptions → `AccessStatus`, sans contournement (FR-008/010/011) (dépend de T012)
- [ ] T020 [US2] Créer la fenêtre principale `pilottelega/ui/main_window.py` : zone multi-lignes + bouton « Récupérer » + `QTabWidget` + indicateur de progression (FR-006, SC-005)
- [ ] T021 [P] [US2] Créer l'onglet de groupe `pilottelega/ui/group_tab.py` : table des membres (`@username` ou repli) + badge de statut d'accès (FR-009/010)
- [ ] T022 [US2] Câbler le flux de récupération dans `main_window` : `parse_links` → `await fetch_group` par groupe → création d'un onglet ; signaler les lignes invalides sans bloquer ; UI réactive (dépend de T018, T019, T020, T021)

**Checkpoint**: US1 + US2 fonctionnent indépendamment.

---

## Phase 5: User Story 3 - Analyser les recoupements (Priority: P3)

**Goal**: onglet Analyse croisant les listes : membres dans un seul groupe vs plusieurs (avec la
liste des `@groupes`).

**Independent Test**: avec ≥ 2 groupes ayant des membres communs, ouvrir Analyse → un membre
commun apparaît en multi-groupes avec la bonne liste, un membre exclusif en « un seul groupe ».

### Tests for User Story 3 ⚠️

- [ ] T023 [P] [US3] Test unitaire `tests/unit/test_analysis.py` : `compute_overlap` (membre commun à 2 groupes, membre exclusif, aucun commun, un seul groupe)

### Implementation for User Story 3

- [ ] T024 [P] [US3] Créer `pilottelega/core/analysis.py` : `compute_overlap(groups)` → `AnalysisResult` (membership en un passage, partition single/multi) (FR-012/013/014) (contracts/analysis-service.md)
- [ ] T025 [US3] Créer l'onglet Analyse `pilottelega/ui/analysis_tab.py` : table « un seul groupe » + table « plusieurs groupes » avec la liste des `@groupes` (FR-013/014)
- [ ] T026 [US3] Intégrer l'onglet Analyse dans `main_window` et le rafraîchir à chaque nouvelle récupération (dépend de T024, T025, T022)

**Checkpoint**: les 3 user stories sont fonctionnelles indépendamment — MVP complet.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: finitions, packaging, validation transverse.

- [ ] T027 [P] Compléter les docstrings (fonctions/classes) et la section usage du `README.md`
- [ ] T028 [P] Créer la config PyInstaller `pilottelega.spec` pour produire l'`.exe` autonome Windows (jalon 5) — aucun secret embarqué
- [ ] T029 Exécuter la validation `quickstart.md` (scénarios S1/S2/S3) de bout en bout via `python -m pilottelega`
- [ ] T030 Vérifier la CI verte en local : `ruff check .`, `black --check .`, `pytest` (Principe V)
- [ ] T031 Vérification confidentialité (SC-006) : aucun `api_id`/`api_hash`/session embarqué dans le build ni transmis hors Telegram

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** : aucune dépendance — démarre immédiatement.
- **Foundational (Phase 2)** : dépend du Setup — BLOQUE toutes les user stories.
- **User Stories (Phase 3+)** : dépendent du Foundational. US1 → US2 → US3 par priorité ;
  US2 et US3 réutilisent `telegram_service`/`models` mais restent testables indépendamment.
- **Polish (Phase 6)** : après les user stories visées.

### User Story Dependencies

- **US1 (P1)** : après Foundational. Aucune dépendance sur une autre story. = MVP.
- **US2 (P2)** : après Foundational. Réutilise `TelegramService` (étend `fetch_group`) ; testable seule.
- **US3 (P3)** : après Foundational. Consomme les `TargetGroup` récupérés (US2) pour la démo end-to-end, mais `compute_overlap` est testable seul sur des données en mémoire.

### Within Each User Story

- Les tests (`tests/`) sont écrits et échouent avant l'implémentation.
- `core/` (modèle/logique) avant `ui/`. Services avant câblage UI.

### Parallel Opportunities

- Setup : T002, T003, T004, T005 en parallèle (fichiers différents).
- Foundational : T006, T007, T008 en parallèle.
- US1 : T011 (test) avant T012.
- US2 : T016, T017, T018 en parallèle ; T021 (group_tab) parallèle à T019/T020.
- US3 : T023, T024 en parallèle.
- Polish : T027, T028 en parallèle.

---

## Parallel Example: Foundational (Phase 2)

```bash
# Lancer en parallèle (fichiers indépendants) :
Task: "core/models.py — dataclasses + AccessStatus (T006)"
Task: "app/paths.py — résolution %APPDATA% (T007)"
Task: "app/logging_conf.py — configuration logging (T008)"
```

## Parallel Example: User Story 2

```bash
# Tests d'abord (échouent) :
Task: "tests/unit/test_link_parser.py (T016)"
Task: "tests/integration/test_telegram_service_fetch.py (T017)"
# Puis logique pure en parallèle de l'UI :
Task: "core/link_parser.py (T018)"
Task: "ui/group_tab.py (T021)"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → 2. Phase 2 Foundational (CRITIQUE) → 3. Phase 3 US1 →
4. **STOP & VALIDATE** : connexion + session persistée (jalon 1 de la roadmap).

### Incremental Delivery

1. Setup + Foundational → socle prêt.
2. + US1 → connexion (MVP, jalon 1).
3. + US2 → saisie + fetch + onglets (jalons 2-3).
4. + US3 → analyse de recoupement (jalon 4, le cœur).
5. Polish → packaging `.exe` (jalon 5).

---

## Notes

- [P] = fichiers différents, sans dépendance.
- `core/` n'importe jamais Qt (testabilité — Principe V ; qasync — Principe III).
- Commit après chaque tâche ou groupe logique (automatisation Git du projet, CLAUDE.md).
- Aucune persistance des membres (en mémoire — Principe IV).
- Total : 31 tâches.
