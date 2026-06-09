"""Tests unitaires de l'export Excel (groupe + analyse)."""

from __future__ import annotations

from openpyxl import load_workbook

from pilottelega.core.analysis import compute_overlap
from pilottelega.core.export import export_analysis_to_xlsx, export_group_to_xlsx
from pilottelega.core.models import AccessStatus, Member, TargetGroup


def _group(handle, members):
    return TargetGroup(
        raw_input=f"@{handle}",
        identifier=f"@{handle}",
        handle=handle,
        access_status=AccessStatus.FULL,
        members=members,
    )


def test_export_group_writes_members(tmp_path):
    group = _group("alpha", [Member(1, "alice", "Alice"), Member(2, None, "Bob")])
    path = tmp_path / "group.xlsx"
    export_group_to_xlsx(group, str(path))

    ws = load_workbook(path).active
    rows = list(ws.iter_rows(values_only=True))
    assert rows[0] == ("group.member_col", "export.username_col", "group.id_col")  # clés brutes
    assert rows[1] == ("Alice", "alice", 1)
    assert rows[2] == ("Bob", None, 2)


def test_export_group_with_translator(tmp_path):
    group = _group("alpha", [Member(1, "alice", "Alice")])
    path = tmp_path / "group_fr.xlsx"
    export_group_to_xlsx(group, str(path), t=lambda k: {"group.member_col": "Membre"}.get(k, k))

    ws = load_workbook(path).active
    assert ws.cell(row=1, column=1).value == "Membre"


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
