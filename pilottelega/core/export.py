"""Export Excel (.xlsx) des membres d'un groupe et du résultat d'analyse.

Logique pure (pas de Qt). Les en-têtes sont fournis via une fonction de traduction ``t``
(par défaut l'identité, ce qui rend le module testable sans i18n).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

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
    "join_date",
    "phone",
    "description",
]


def filter_members(members: Iterable[Member], exclude_bots: bool) -> list[Member]:
    """Renvoie les membres en excluant les bots si ``exclude_bots`` est vrai."""
    if not exclude_bots:
        return list(members)
    return [m for m in members if not m.is_bot]


def member_row(member: Member) -> list[object]:
    """Ligne de valeurs d'un membre, dans l'ordre de :data:`GROUP_COLUMNS`."""
    return [
        member.user_id,
        f"@{member.username}" if member.username else "",
        member.first_name or "",
        member.last_name or "",
        member.is_bot,
        member.is_premium,
        member.is_deleted,
        member.last_seen or "",
        member.join_date or "",
        member.phone or "",
        member.description or "",
    ]


def _sheet_name(name: str) -> str:
    return name[:_MAX_SHEET_NAME]


def export_rows_to_xlsx(
    headers: list[str],
    rows: Iterable[list[object]],
    path: str,
    sheet_title: str = "Sheet1",
) -> None:
    """Écrit une table simple (en-têtes + lignes) dans un ``.xlsx`` (générique, réutilisable)."""
    wb = Workbook()
    ws = wb.active
    ws.title = _sheet_name(sheet_title)
    ws.append(list(headers))
    for row in rows:
        ws.append(list(row))
    wb.save(path)


def export_group_to_xlsx(
    group: TargetGroup,
    path: str,
    t: Callable[[str], str] = lambda k: k,
    exclude_bots: bool = False,
) -> None:
    """Écrit les membres d'un ``TargetGroup`` dans un fichier ``.xlsx`` (toutes colonnes).

    Si ``exclude_bots`` est vrai, les comptes bots sont omis du fichier.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = _sheet_name(t("export.sheet_group"))
    ws.append(GROUP_COLUMNS)
    for member in filter_members(group.members, exclude_bots):
        ws.append(member_row(member))
    wb.save(path)


def export_analysis_to_xlsx(
    result: AnalysisResult, path: str, t: Callable[[str], str] = lambda k: k
) -> None:
    """Écrit l'analyse de recoupement dans un ``.xlsx`` à deux onglets.

    Chaque onglet contient **toutes les colonnes membres** (:data:`GROUP_COLUMNS`) plus une
    colonne ``groups``. Onglet 1 : membres présents dans un seul groupe. Onglet 2 : membres
    présents dans plusieurs groupes (colonne ``groups`` = liste des ``@groupes``).
    """
    wb = Workbook()

    # Feuille « un seul groupe » : colonnes membres + une colonne du groupe.
    ws_single = wb.active
    ws_single.title = _sheet_name(t("export.sheet_single"))
    ws_single.append([*GROUP_COLUMNS, "group1"])
    for member, group_label in result.single_group:
        ws_single.append([*member_row(member), group_label])

    # Feuille « multi-groupes » : colonnes membres + une colonne PAR groupe (group1, group2, …).
    ws_multi = wb.create_sheet(_sheet_name(t("export.sheet_multi")))
    max_groups = max((len(labels) for _, labels in result.multi_group), default=0)
    max_groups = max(max_groups, 1)  # au moins une colonne group1
    group_headers = [f"group{i}" for i in range(1, max_groups + 1)]
    ws_multi.append([*GROUP_COLUMNS, *group_headers])
    for member, group_labels in result.multi_group:
        padded = [*group_labels, *([""] * (max_groups - len(group_labels)))]
        ws_multi.append([*member_row(member), *padded])

    # Feuille « tous les utilisateurs » : liste dédupliquée, toutes colonnes, SANS groupe.
    ws_all = wb.create_sheet(_sheet_name(t("export.sheet_all")))
    ws_all.append(list(GROUP_COLUMNS))
    seen: set[int] = set()
    for member, _info in (*result.single_group, *result.multi_group):
        if member.user_id in seen:
            continue
        seen.add(member.user_id)
        ws_all.append(member_row(member))

    wb.save(path)
