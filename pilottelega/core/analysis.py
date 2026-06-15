"""Calcul du recoupement inter-groupes (logique pure, cœur du produit — FR-012/013/014)."""

from __future__ import annotations

from collections.abc import Iterable

from pilottelega.core.models import AnalysisResult, Member, TargetGroup


def compute_overlap(groups: Iterable[TargetGroup], exclude_bots: bool = False) -> AnalysisResult:
    """Croise les membres des groupes en un seul passage.

    Construit ``membership`` (``user_id`` → ensemble des étiquettes de groupes), puis
    partitionne : présence dans **un seul** groupe vs **plusieurs** (avec la liste triée
    des ``@groupes``). L'identité repose sur ``user_id`` (FR-012). Si ``exclude_bots`` est
    vrai, les comptes bots sont écartés des listes.
    """
    membership: dict[int, set[str]] = {}
    members_by_id: dict[int, Member] = {}

    for group in groups:
        label = group.label
        for member in group.members:
            if exclude_bots and member.is_bot:
                continue
            membership.setdefault(member.user_id, set()).add(label)
            members_by_id.setdefault(member.user_id, member)

    single_group: list[tuple[Member, str]] = []
    multi_group: list[tuple[Member, list[str]]] = []

    for user_id, labels in membership.items():
        member = members_by_id[user_id]
        if len(labels) == 1:
            single_group.append((member, next(iter(labels))))
        else:
            multi_group.append((member, sorted(labels)))

    return AnalysisResult(
        membership=membership,
        single_group=single_group,
        multi_group=multi_group,
    )
