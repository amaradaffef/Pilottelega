"""Historique des retraits effectués (modèle pur, testable sans Qt ni réseau).

Chaque exécution de retrait produit des enregistrements ``RemovalRecord`` (un par membre,
avec le résultat). La persistance locale est gérée par :mod:`pilottelega.app.history_store`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from pilottelega.core.removal import RemovalResult

ACTION_BAN = "ban"
ACTION_KICK = "kick"


@dataclass(frozen=True)
class RemovalRecord:
    """Une action de retrait consignée : un membre, un groupe, un résultat, une date."""

    timestamp: str  # ISO 8601 (ex. « 2026-07-02T12:34:56 »)
    user_id: int
    user_label: str
    group_identifier: str
    group_label: str
    action: str  # ACTION_BAN ou ACTION_KICK
    ok: bool
    error: str | None = None


def records_from_results(
    results: Iterable[RemovalResult], ban: bool, timestamp: str
) -> list[RemovalRecord]:
    """Convertit les résultats d'une exécution en enregistrements d'historique."""
    action = ACTION_BAN if ban else ACTION_KICK
    records: list[RemovalRecord] = []
    for result in results:
        removal = result.removal
        records.append(
            RemovalRecord(
                timestamp=timestamp,
                user_id=removal.user_id,
                user_label=removal.user_label,
                group_identifier=removal.group_identifier,
                group_label=removal.group_label,
                action=action,
                ok=result.ok,
                error=result.error,
            )
        )
    return records


def record_to_dict(record: RemovalRecord) -> dict[str, Any]:
    """Sérialise un enregistrement en dictionnaire JSON-compatible."""
    return {
        "timestamp": record.timestamp,
        "user_id": record.user_id,
        "user_label": record.user_label,
        "group_identifier": record.group_identifier,
        "group_label": record.group_label,
        "action": record.action,
        "ok": record.ok,
        "error": record.error,
    }


def record_from_dict(data: dict[str, Any]) -> RemovalRecord | None:
    """Reconstruit un enregistrement depuis un dictionnaire (``None`` si invalide)."""
    try:
        return RemovalRecord(
            timestamp=str(data["timestamp"]),
            user_id=int(data["user_id"]),
            user_label=str(data["user_label"]),
            group_identifier=str(data["group_identifier"]),
            group_label=str(data["group_label"]),
            action=str(data.get("action", ACTION_KICK)),
            ok=bool(data["ok"]),
            error=(str(data["error"]) if data.get("error") is not None else None),
        )
    except (KeyError, TypeError, ValueError):
        return None
