"""Tests unitaires de l'export Excel (groupe + analyse)."""

from __future__ import annotations

from openpyxl import load_workbook

from pilottelega.core.analysis import compute_overlap
from pilottelega.core.export import (
    GROUP_COLUMNS,
    export_analysis_to_xlsx,
    export_group_to_xlsx,
)
from pilottelega.core.models import AccessStatus, Member, TargetGroup


def _group(handle, members):
    return TargetGroup(
        raw_input=f"@{handle}",
        identifier=f"@{handle}",
        handle=handle,
        access_status=AccessStatus.FULL,
        members=members,
    )


def test_export_group_writes_all_fields(tmp_path):
    members = [
        Member(
            user_id=1,
            username="alice",
            display_name="Alice A",
            first_name="Alice",
            last_name="A",
            is_premium=True,
            last_seen="2026-06-01T10:00:00",
            phone="+33123456789",
            description="Hello, je suis Alice.",
        ),
        Member(user_id=2, username=None, display_name="Botty", first_name="Botty", is_bot=True),
    ]
    group = _group("alpha", members)
    path = tmp_path / "group.xlsx"
    export_group_to_xlsx(group, str(path))

    ws = load_workbook(path).active
    rows = list(ws.iter_rows(values_only=True))
    # En-têtes = tous les champs demandés, dans l'ordre.
    assert list(rows[0]) == GROUP_COLUMNS
    assert rows[0] == (
        "user_id",
        "username",
        "first_name",
        "last_name",
        "is_bot",
        "is_premium",
        "is_deleted",
        "last_seen",
        "phone",
        "description",
    )
    # Alice : premium, dernière connexion datée, téléphone et bio.
    assert rows[1] == (
        1,
        "alice",
        "Alice",
        "A",
        False,
        True,
        False,
        "2026-06-01T10:00:00",
        "+33123456789",
        "Hello, je suis Alice.",
    )
    # Bob : bot, champs absents relus None par openpyxl.
    assert rows[2] == (2, None, "Botty", None, True, False, False, None, None, None)


def test_export_analysis_two_sheets(tmp_path):
    alice, bob, carol = Member(1, "alice"), Member(2, "bob"), Member(3, "carol")
    g1 = _group("alpha", [alice, bob])
    g2 = _group("bravo", [bob, carol])
    result = compute_overlap([g1, g2])

    path = tmp_path / "analyse.xlsx"
    export_analysis_to_xlsx(result, str(path))

    wb = load_workbook(path)
    assert len(wb.worksheets) == 2

    single_rows = list(wb.worksheets[0].iter_rows(min_row=2, values_only=True))
    single_ids = {label for _, label in single_rows}
    assert single_ids  # alice et carol sont uniques

    multi_rows = list(wb.worksheets[1].iter_rows(min_row=2, values_only=True))
    # bob est présent dans les deux groupes
    assert any(
        "@alpha" in (cells[1] or "") and "@bravo" in (cells[1] or "") for cells in multi_rows
    )
