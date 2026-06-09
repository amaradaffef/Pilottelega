# Pilottelega

Application **desktop Windows** (Python) qui récupère les membres de vos groupes Telegram
accessibles et analyse leurs **recoupements** : qui n'est que dans un seul groupe, qui est
présent dans plusieurs (et lesquels).

> Projet **public et gratuit** sous licence [MIT](LICENSE).

**Multi-langue** : interface en **Français / English / Русский** (sélecteur en haut de
fenêtre, langue mémorisée). **Export Excel** : chaque onglet de groupe et l'onglet Analyse
exportent leurs données en `.xlsx`.

## Conformité & confidentialité

- L'application ne lit **que** ce que votre compte peut légitimement consulter et **affiche
  le statut d'accès** de chaque groupe (complet / membres masqués / admin requis). Elle ne
  contourne aucune restriction.
- Vos identifiants d'accès (`api_id`/`api_hash`) et votre session sont stockés **uniquement
  en local** (`%APPDATA%/Pilottelega/`), jamais embarqués dans l'exécutable ni transmis.
- Usage prévu : gestion/analyse de **vos propres** communautés (base légale RGPD), pas de
  prospection non sollicitée.

## Stack technique

PySide6 (UI) · Telethon (API Telegram) · qasync (pont asyncio/Qt) · traitement en mémoire ·
PyInstaller pour la distribution `.exe`.

## Prérequis

- Windows 10/11, Python 3.11+.
- Un compte Telegram et un identifiant d'accès personnel **gratuit** généré sur la page
  officielle « API development tools » de Telegram (`https://my.telegram.org`).

## Installation (développement)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancer l'application

```powershell
python -m pilottelega
```

Au **premier lancement**, un écran d'onboarding vous guide pour saisir vos identifiants et
vous connecter (code + mot de passe 2FA si activé). La session est mémorisée : les lancements
suivants ouvrent directement l'écran principal.

## Qualité

```powershell
ruff check .
black --check .
pytest
```

La logique métier (`pilottelega/core/`) est isolée de l'interface et testée sans réseau ni Qt.
La CI GitHub Actions rejoue ces trois commandes à chaque push / PR.

## Structure

```text
pilottelega/
  core/   # modèle + logique pure (testable) : models, link_parser, analysis, telegram_service
  ui/     # PySide6 : onboarding, fenêtre principale, onglets groupe/analyse
  app/    # config locale, chemins, logging, bootstrap qasync
tests/    # unit/ (logique pure) + integration/ (service Telegram via mocks)
```

Voir les spécifications détaillées dans [`specs/001-members-overlap/`](specs/001-members-overlap/).
