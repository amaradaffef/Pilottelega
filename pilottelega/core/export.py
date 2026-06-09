"""Export Excel (.xlsx) des membres d'un groupe et du résultat d'analyse.

Logique pure (pas de Qt). Les en-têtes sont fournis via une fonction de traduction ``t``
(par défaut l'identité, ce qui rend le module testable sans i18n).
"""

from __future__ import annotations

from collections.abc import Callable

from openpyxl import Workbook

from pilottelega.core.models import AnalysisResult, Member, TargetGroup

# Excel limite les noms d'onglets à 31 caractères.
_MAX_SHEET_NAME = 31

# Colonnes des membres (en-têtes techniques, identiques à l'export et à la table UI).
GROUP_COLUMNS: list[str] = [
    "user_id",
    "username",
    "first_name",
    "last_name",
    "is_bot",
    "is_premium",
    "is_deleted",
    "last_seen",
]


def member_row(member: Member) -> list[object]:
    """Ligne de valeurs d'un membre, dans l'ordre de :data:`GROUP_COLUMNS`."""
    return [
        member.user_id,
        member.username or "",
        member.first_name or "",
        member.last_name or "",
        member.is_bot,
        member.is_premium,
        member.is_deleted,
        member.last_seen or "",
    ]


def _sheet_name(name: str) -> str:
    return name[:_MAX_SHEET_NAME]


def export_group_to_xlsx(
    group: TargetGroup, path: str, t: Callable[[str], str] = lambda k: k
) -> None:
    """Écrit les membres d'un ``TargetGroup`` dans un fichier ``.xlsx`` (toutes colonnes)."""
    wb = Workbook()
    ws = wb.active
    ws.title = _sheet_name(t("export.sheet_group"))
    ws.append(GROUP_COLUMNS)
    for member in group.members:
        ws.append(member_row(member))
    wb.save(path)


def export_analysis_to_xlsx(
    result: AnalysisResult, path: str, t: Callable[[str], str] = lambda k: k
) -> None:
    """Écrit l'analyse de recoupement dans un ``.xlsx`` à deux onglets.

    Onglet 1 : membres présents dans un seul groupe. Onglet 2 : membres multi-groupes
    avec la liste des groupes.
    """
    wb = Workbook()

    ws_single = wb.active
    ws_single.title = _sheet_name(t("export.sheet_single"))
    ws_single.append([t("analysis.member_col"), t("analysis.group_col")])
    for member, group_label in result.single_group:
        ws_single.append([member.label, group_label])

    ws_multi = wb.create_sheet(_sheet_name(t("export.sheet_multi")))
    ws_multi.append([t("analysis.member_col"), t("analysis.groups_col")])
    for member, group_labels in result.multi_group:
        ws_multi.append([member.label, ", ".join(group_labels)])

    wb.save(path)
