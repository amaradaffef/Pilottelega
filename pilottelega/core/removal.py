"""Planification du retrait de membres de groupes (logique pure, testable).

On ne fait QUE calculer ici *qui retirer de quel groupe* ; l'exécution réelle (kick/ban)
est dans :mod:`pilottelega.core.telegram_service`. Deux stratégies :

- **Masse** : on choisit UN groupe à conserver ; chaque membre présent dans ce groupe
  ET dans d'autres est retiré des autres (jamais du groupe conservé). Les membres absents
  du groupe conservé ne sont **pas** touchés (sécurité).
- **Par utilisateur** : on fournit explicitement, pour un membre, les groupes d'où le retirer.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pilottelega.core.models import Member, TargetGroup


@dataclass(frozen=True)
class Removal:
    """Un retrait à effectuer : un membre, d'un groupe précis."""

    group_identifier: str
    group_label: str
    user_id: int
    user_label: str


@dataclass
class RemovalResult:
    """Résultat de l'exécution d'un :class:`Removal`."""

    removal: Removal
    ok: bool
    error: str | None = None


def _membership(
    groups: Iterable[TargetGroup],
) -> tuple[dict[int, list[tuple[str, str]]], dict[int, Member]]:
    """Construit ``user_id -> [(identifier, label)…]`` et ``user_id -> Member``."""
    membership: dict[int, list[tuple[str, str]]] = {}
    members: dict[int, Member] = {}
    for group in groups:
        for member in group.members:
            entry = (group.identifier, group.label)
            bucket = membership.setdefault(member.user_id, [])
            if group.identifier not in {gi for gi, _ in bucket}:
                bucket.append(entry)
            members.setdefault(member.user_id, member)
    return membership, members


def plan_mass_removal(groups: Iterable[TargetGroup], keep_identifier: str) -> list[Removal]:
    """Retraits pour ne garder chaque membre multi-groupes que dans ``keep_identifier``.

    Un membre n'est traité que s'il est présent dans le groupe à conserver ; il est alors
    retiré de tous ses autres groupes. Les membres absents du groupe conservé sont ignorés.
    """
    membership, members = _membership(groups)
    removals: list[Removal] = []
    for user_id, group_list in membership.items():
        identifiers = [gi for gi, _ in group_list]
        if len(identifiers) <= 1:
            continue
        if keep_identifier not in identifiers:
            continue
        for identifier, label in group_list:
            if identifier != keep_identifier:
                removals.append(Removal(identifier, label, user_id, members[user_id].label))
    return removals


def plan_user_removal(
    groups: Iterable[TargetGroup], user_id: int, remove_identifiers: Iterable[str]
) -> list[Removal]:
    """Retraits explicites d'un membre donné depuis les groupes listés."""
    membership, members = _membership(groups)
    if user_id not in members:
        return []
    user_label = members[user_id].label
    id_to_label = {gi: label for bucket in membership.values() for gi, label in bucket}
    wanted = {gi for gi, _ in membership[user_id]}  # uniquement ses groupes réels
    return [
        Removal(identifier, id_to_label.get(identifier, identifier), user_id, user_label)
        for identifier in remove_identifiers
        if identifier in wanted
    ]
