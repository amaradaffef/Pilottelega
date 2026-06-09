"""Lecture/écriture **locale** de la configuration utilisateur.

Stocke ``api_id`` / ``api_hash`` / ``phone`` dans ``%APPDATA%/Pilottelega/config.json``.
Ces valeurs ne quittent jamais le poste (Principe II / FR-004).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pilottelega.app import paths
from pilottelega.app.logging_conf import get_logger

logger = get_logger(__name__)


@dataclass
class AppConfig:
    """Identifiants d'accès personnels saisis par l'utilisateur."""

    api_id: int
    api_hash: str
    phone: str

    def is_complete(self) -> bool:
        """Vrai si les trois champs sont renseignés."""
        return bool(self.api_id and self.api_hash and self.phone)


def load_config(path: Path | None = None) -> AppConfig | None:
    """Charge la configuration locale, ou ``None`` si absente/illisible."""
    cfg_path = path or paths.config_path()
    if not cfg_path.exists():
        return None
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        return AppConfig(
            api_id=int(data["api_id"]),
            api_hash=str(data["api_hash"]),
            phone=str(data["phone"]),
        )
    except (ValueError, KeyError, OSError) as exc:
        # On ne journalise jamais le contenu (secrets) — uniquement l'événement.
        logger.warning("Configuration locale illisible: %s", type(exc).__name__)
        return None


def save_config(config: AppConfig, path: Path | None = None) -> None:
    """Écrit la configuration locale (création du dossier si nécessaire)."""
    cfg_path = path or paths.config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Configuration locale enregistrée.")
