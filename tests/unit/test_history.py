"""Tests unitaires du modèle d'historique des retraits (logique pure)."""

from __future__ import annotations

from pilottelega.core.history import (
    ACTION_BAN,
    ACTION_KICK,
    record_from_dict,
    record_to_dict,
    records_from_results,
)
from pilottelega.core.removal import Removal, RemovalResult


def _result(ok: bool, error: str | None = None) -> RemovalResult:
    removal = Removal("@bravo", "bravo", 1, "@neo", 555, "neo")
    return RemovalResult(removal, ok=ok, error=error)


def test_records_from_results_maps_fields_and_action():
    results = [_result(ok=True), _result(ok=False, error="boom")]
    records = records_from_results(results, ban=True, timestamp="2026-07-02T12:00:00")
    assert [r.action for r in records] == [ACTION_BAN, ACTION_BAN]
    assert records[0].timestamp == "2026-07-02T12:00:00"
    assert records[0].user_label == "@neo"
    assert records[0].group_label == "bravo"
    assert records[0].ok is True
    assert records[1].ok is False
    assert records[1].error == "boom"


def test_records_from_results_kick_action():
    records = records_from_results([_result(ok=True)], ban=False, timestamp="t")
    assert records[0].action == ACTION_KICK


def test_record_dict_round_trip():
    record = records_from_results([_result(ok=False, error="x")], ban=True, timestamp="t")[0]
    restored = record_from_dict(record_to_dict(record))
    assert restored == record


def test_record_from_dict_invalid_returns_none():
    assert record_from_dict({"timestamp": "t"}) is None  # champs manquants
