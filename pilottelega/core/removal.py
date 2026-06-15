"""Planification du retrait de membres de groupes (logique pure, testable).

On ne fait QUE calculer ici *qui retirer de quel groupe* ; l'exécution réelle (kick/ban)
est dans :mod:`pilottelega.core.telegram_service`. Deux stratégies :

- **Masse** : on choisit UN groupe à conserver ; chaque membre présent dans ce groupe
  ET dans d'autres est retiré des autres (jamais du groupe conservé). Les membres absents
  du groupe conservé ne sont **pas** touchés (sécurité).
- **Par utilisateur** : on fournit explicitement, pour un membre, les groupes d'où le retirer.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

from pilottelega.core.models import Member, TargetGroup

# Préfixes de lien éventuels à retirer d'un compte protégé saisi (ex. « t.me/moi »).
_LINK_PREFIXES: tuple[str, ...] = ("https://", "http://", "t.me/", "telegram.me/")
# Séparateurs acceptés dans le champ « mes comptes » (virgule, espace, point-virgule, saut).
_SPLIT = re.compile(r"[\s,;]+")


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


def parse_protected(raw: str) -> tuple[frozenset[int], frozenset[str]]:
    """Analyse la saisie « mes comptes » en ``(ids, usernames)``.

    Chaque jeton peut être un ``@username``, un ``username`` nu, un identifiant numérique
    ou un lien ``t.me/...``. Les noms d'utilisateur sont normalisés en minuscules (sans ``@``)
    pour une comparaison insensible à la casse ; les jetons numériques deviennent des ids.
    """
    ids: set[int] = set()
    usernames: set[str] = set()
    for token in _SPLIT.split(raw.strip()):
        if not token:
            continue
        # Retire les préfixes de lien empilés (ex. « https://t.me/moi »), puis « @ » et « / ».
        changed = True
        while changed:
            changed = False
            for prefix in _LINK_PREFIXES:
                if token.lower().startswith(prefix):
                    token = token[len(prefix) :]
                    changed = True
        token = token.lstrip("@").strip("/")
        if not token:
            continue
        if token.isdigit():
            ids.add(int(token))
        else:
            usernames.add(token.lower())
    return frozenset(ids), frozenset(usernames)


@dataclass(frozen=True)
class RemovalFilter:
    """Politique de protection appliquée aux retraits (et listes).

    - ``protected_ids`` / ``protected_usernames`` : « mes comptes » à ne **jamais** retirer.
    - ``exclude_bots`` : si vrai, les bots sont exclus des listes et jamais retirés.
    """

    protected_ids: frozenset[int] = field(default_factory=frozenset)
    protected_usernames: frozenset[str] = field(default_factory=frozenset)
    exclude_bots: bool = True

    @classmethod
    def from_raw(cls, raw: str, exclude_bots: bool = True) -> RemovalFilter:
        """Construit un filtre depuis la saisie brute du champ « mes comptes »."""
        ids, usernames = parse_protected(raw)
        return cls(protected_ids=ids, protected_usernames=usernames, exclude_bots=exclude_bots)

    def is_protected(self, member: Member) -> bool:
        """Vrai si le membre fait partie des comptes protégés de l'utilisateur."""
        if member.user_id in self.protected_ids:
            return True
        return bool(member.username and member.username.lower() in self.protected_usernames)

    def is_excluded(self, member: Member) -> bool:
        """Vrai si le membre ne doit jamais être retiré (protégé ou bot exclu)."""
        if self.exclude_bots and member.is_bot:
            return True
        return self.is_protected(member)


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


def plan_mass_removal(
    groups: Iterable[TargetGroup],
    keep_identifier: str,
    filter_: RemovalFilter | None = None,
) -> list[Removal]:
    """Retraits pour ne garder chaque membre multi-groupes que dans ``keep_identifier``.

    Un membre n'est traité que s'il est présent dans le groupe à conserver ; il est alors
    retiré de tous ses autres groupes. Les membres absents du groupe conservé sont ignorés.
    Les comptes protégés et (si activé) les bots ne sont jamais retirés (``filter_``).
    """
    filter_ = filter_ or RemovalFilter()
    membership, members = _membership(groups)
    removals: list[Removal] = []
    for user_id, group_list in membership.items():
        if filter_.is_excluded(members[user_id]):
            continue
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
    groups: Iterable[TargetGroup],
    user_id: int,
    remove_identifiers: Iterable[str],
    filter_: RemovalFilter | None = None,
) -> list[Removal]:
    """Retraits explicites d'un membre donné depuis les groupes listés.

    Un compte protégé ou un bot exclu (``filter_``) n'est jamais retiré : on renvoie ``[]``.
    """
    filter_ = filter_ or RemovalFilter()
    membership, members = _membership(groups)
    if user_id not in members:
        return []
    if filter_.is_excluded(members[user_id]):
        return []
    user_label = members[user_id].label
    id_to_label = {gi: label for bucket in membership.values() for gi, label in bucket}
    wanted = {gi for gi, _ in membership[user_id]}  # uniquement ses groupes réels
    return [
        Removal(identifier, id_to_label.get(identifier, identifier), user_id, user_label)
        for identifier in remove_identifiers
        if identifier in wanted
    ]
