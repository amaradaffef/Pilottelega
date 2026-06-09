"""Préférences d'interface locales (langue), indépendantes des identifiants.

Stockées dans ``%APPDATA%/Pilottelega/prefs.json`` afin d'être disponibles dès le
premier lancement, avant toute connexion.
"""

from __future__ import annotations

import json
from pathlib import Path

from pilottelega.app import paths
from pilottelega.app.i18n import DEFAULT_LANGUAGE
from pilottelega.app.logging_conf import get_logger

logger = get_logger(__name__)

PREFS_FILE_NAME = "prefs.json"


def prefs_path() -> Path:
    """Chemin du fichier de préférences local."""
    return paths.app_data_dir() / PREFS_FILE_NAME


def load_language() -> str:
    """Retourne la langue enregistrée, ou la langue par défaut si absente/illisible."""
    path = prefs_path()
    if not path.exists():
        return DEFAULT_LANGUAGE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("language", DEFAULT_LANGUAGE))
    except (ValueError, OSError) as exc:
        logger.warning("Préférences illisibles: %s", type(exc).__name__)
        return DEFAULT_LANGUAGE


def save_language(lang: str) -> None:
    """Enregistre la langue choisie."""
    path = prefs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"language": lang}, ensure_ascii=False), encoding="utf-8")
