"""Préférences d'interface locales (langue, filtres), indépendantes des identifiants.

Stockées dans ``%APPDATA%/Pilottelega/prefs.json`` afin d'être disponibles dès le
premier lancement, avant toute connexion. Chaque écriture relit puis fusionne le fichier
pour ne pas écraser les autres clés.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pilottelega.app import paths
from pilottelega.app.i18n import DEFAULT_LANGUAGE
from pilottelega.app.logging_conf import get_logger

logger = get_logger(__name__)

PREFS_FILE_NAME = "prefs.json"


def prefs_path() -> Path:
    """Chemin du fichier de préférences local."""
    return paths.app_data_dir() / PREFS_FILE_NAME


def _load() -> dict[str, Any]:
    """Charge l'intégralité des préférences (dictionnaire vide si absent/illisible)."""
    path = prefs_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError) as exc:
        logger.warning("Préférences illisibles: %s", type(exc).__name__)
        return {}


def _save(key: str, value: Any) -> None:
    """Met à jour une clé en préservant les autres (lecture-fusion-écriture)."""
    data = _load()
    data[key] = value
    path = prefs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def load_language() -> str:
    """Retourne la langue enregistrée, ou la langue par défaut si absente/illisible."""
    return str(_load().get("language", DEFAULT_LANGUAGE))


def save_language(lang: str) -> None:
    """Enregistre la langue choisie."""
    _save("language", lang)


def load_protected_accounts() -> str:
    """Retourne la saisie « mes comptes à ne jamais retirer » (chaîne brute)."""
    return str(_load().get("protected_accounts", ""))


def save_protected_accounts(raw: str) -> None:
    """Enregistre la saisie « mes comptes à ne jamais retirer »."""
    _save("protected_accounts", raw)


def load_exclude_bots() -> bool:
    """Retourne la préférence d'exclusion des bots (activée par défaut)."""
    return bool(_load().get("exclude_bots", True))


def save_exclude_bots(value: bool) -> None:
    """Enregistre la préférence d'exclusion des bots."""
    _save("exclude_bots", value)
