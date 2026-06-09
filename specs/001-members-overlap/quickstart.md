# Quickstart — Pilottelega (validation MVP)

Guide pour lancer l'application en développement et valider le flux de bout en bout.
La logique se valide via `python` **avant** tout packaging (jalons 1→4 ; le `.exe` est le jalon 5).

## Prérequis

- Windows 10/11, Python 3.11+.
- Un compte Telegram et un **identifiant d'accès personnel** (`api_id` / `api_hash`) généré
  sur la page officielle « API development tools » de Telegram (gratuit).

## Installation (dev)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt    # PySide6, Telethon, qasync (+ dev: pytest, ruff, black)
```

## Lancer l'application

```powershell
python -m pilottelega
```

## Scénarios de validation

### S1 — Onboarding & connexion (User Story 1 / FR-001→005)

1. Premier lancement sur un profil vierge → l'écran d'onboarding s'affiche avec le lien vers
   la page de génération de l'identifiant.
2. Saisir `api_id`, `api_hash`, numéro → recevoir le code dans Telegram → le saisir → (2FA si
   activée) saisir le mot de passe.
3. **Attendu** : connexion réussie, session écrite sous `%APPDATA%/Pilottelega/`.
4. Fermer puis relancer → **attendu** : l'écran principal s'ouvre sans ressaisie (SC-002).

### S2 — Saisie de groupes & récupération (User Story 2 / FR-006→010)

1. Coller plusieurs liens de groupes (un par ligne ; formes `@nom`, `t.me/...`).
2. Lancer la récupération.
3. **Attendu** : un onglet par groupe, chacun listant ses membres et un **statut d'accès**
   (FULL / PARTIAL_HIDDEN / ADMIN_REQUIRED / ERROR) cohérent ; l'UI reste réactive (SC-005) ;
   une ligne invalide est signalée sans bloquer les autres.

### S3 — Analyse de recoupement (User Story 3 / FR-013/014)

1. Avec ≥ 2 groupes ayant des membres communs, ouvrir l'onglet **Analyse**.
2. **Attendu** :
   - vue « un seul groupe » : un membre exclusif y figure ;
   - vue « plusieurs groupes » : un membre commun y figure avec la liste exacte des `@groupes` ;
   - aucun membre commun → vue multi-groupes vide (SC-004).

## Vérifications qualité (Principe V / standards CLAUDE.md)

```powershell
ruff check .
black --check .
pytest
```

- Les tests **unitaires** (`tests/unit/`) couvrent `link_parser` et `analysis` sans réseau ni Qt.
- Les tests **d'intégration** (`tests/integration/`) couvrent `telegram_service` avec des mocks
  Telethon (chaque `AccessStatus`).
- **Attendu** : Ruff et Black sans erreur, pytest vert. La CI GitHub Actions rejoue ces trois
  commandes à chaque push/PR.

## Vérification confidentialité (SC-006)

- Inspecter le `.exe`/build : aucun `api_id`/`api_hash`/session embarqué.
- Aucune sortie réseau hors Telegram ; identifiants et session présents uniquement sous
  `%APPDATA%/Pilottelega/`.
```
