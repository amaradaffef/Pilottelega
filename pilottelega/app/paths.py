"""Résolution des chemins de stockage **local** de Pilottelega.

Les identifiants et la session vivent sous ``%APPDATA%/Pilottelega/`` (jamais embarqués
dans l'exécutable — Principe II / FR-004).
"""

from __future__ import annotations

import os
from pathlib import Path

APP_DIR_NAME = "Pilottelega"
CONFIG_FILE_NAME = "config.json"
SESSION_FILE_NAME = "pilottelega.session"


def app_data_dir() -> Path:
    """Répertoire de données de l'application, créé si nécessaire.

    Utilise ``%APPDATA%`` sous Windows, avec repli sur ``~/.config`` ailleurs (dev).
    """
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    path = root / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    """Chemin du fichier de configuration local (``api_id``/``api_hash``/téléphone)."""
    return app_data_dir() / CONFIG_FILE_NAME


def session_path() -> Path:
    """Chemin du fichier de session Telethon local."""
    return app_data_dir() / SESSION_FILE_NAME
