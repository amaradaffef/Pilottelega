"""Persistance locale de l'historique des retraits.

Stocké dans ``%APPDATA%/Pilottelega/history.json`` (jamais embarqué dans l'exécutable).
Le fichier est borné à ``MAX_RECORDS`` entrées pour ne pas croître indéfiniment.
"""

from __future__ import annotations

import json
from pathlib import Path

from pilottelega.app import paths
from pilottelega.app.logging_conf import get_logger
from pilottelega.core.history import RemovalRecord, record_from_dict, record_to_dict

logger = get_logger(__name__)

HISTORY_FILE_NAME = "history.json"
MAX_RECORDS = 5000  # borne raisonnable (les plus anciens sont oubliés au-delà)


def history_path() -> Path:
    """Chemin du fichier d'historique local."""
    return paths.app_data_dir() / HISTORY_FILE_NAME


def load_history() -> list[RemovalRecord]:
    """Charge l'historique (liste vide si absent/illisible)."""
    path = history_path()
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        logger.warning("Historique illisible: %s", type(exc).__name__)
        return []
    if not isinstance(raw, list):
        return []
    records = [record_from_dict(item) for item in raw if isinstance(item, dict)]
    return [r for r in records if r is not None]


def _write(records: list[RemovalRecord]) -> None:
    """Écrit l'historique (borné à ``MAX_RECORDS``, les plus récents conservés)."""
    trimmed = records[-MAX_RECORDS:]
    path = history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [record_to_dict(r) for r in trimmed]
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def append_records(records: list[RemovalRecord]) -> None:
    """Ajoute des enregistrements à l'historique existant."""
    if not records:
        return
    existing = load_history()
    existing.extend(records)
    _write(existing)


def clear_history() -> None:
    """Vide l'historique."""
    _write([])
