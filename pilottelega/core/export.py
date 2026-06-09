"""Export Excel (.xlsx) des membres d'un groupe et du résultat d'analyse.

Logique pure (pas de Qt). Les en-têtes sont fournis via une fonction de traduction ``t``
(par défaut l'identité, ce qui rend le module testable sans i18n).
"""

from __future__ import annotations

from collections.abc import Callable

from openpyxl import Workbook

from pilottelega.core.models import AnalysisResult, TargetGroup

# Excel limite les noms d'onglets à 31 caractères.
_MAX_SHEET_NAME = 31


def _sheet_name(name: str) -> str:
    return name[:_MAX_SHEET_NAME]


def export_group_to_xlsx(
    group: TargetGroup, path: str, t: Callable[[str], str] = lambda k: k
) -> None:
    """Écrit les membres d'un ``TargetGroup`` dans un fichier ``.xlsx``."""
    wb = Workbook()
    ws = wb.active
    ws.title = _sheet_name(t("export.sheet_group"))
    ws.append([t("group.member_col"), t("export.username_col"), t("group.id_col")])
    for member in group.members:
        ws.append([member.display_name or "", member.username or "", member.user_id])
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
