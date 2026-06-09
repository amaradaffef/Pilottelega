"""Modèle de données en mémoire de Pilottelega.

Aucune dépendance Qt ni réseau : ce module est 100% testable (Principe V de la
constitution). Les données métier ne sont pas persistées (Principe IV — MVP en mémoire).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class AccessStatus(StrEnum):
    """Niveau de lecture obtenu sur un groupe (FR-010).

    L'application n'essaie jamais de contourner une restriction : elle rapporte
    seulement le statut réel (FR-011).
    """

    FULL = "full"  # Liste complète des membres lue
    PARTIAL_HIDDEN = "partial_hidden"  # Membres masqués → liste partielle (voire vide)
    ADMIN_REQUIRED = "admin_required"  # Droits administrateur requis pour lister
    ERROR = "error"  # Échec (réseau, entrée invalide, session expirée…)

    @property
    def label(self) -> str:
        """Libellé lisible pour l'interface."""
        return {
            AccessStatus.FULL: "Accès complet",
            AccessStatus.PARTIAL_HIDDEN: "Membres masqués",
            AccessStatus.ADMIN_REQUIRED: "Droits administrateur requis",
            AccessStatus.ERROR: "Erreur",
        }[self]


@dataclass(frozen=True)
class Member:
    """Une personne appartenant à un ou plusieurs groupes.

    L'identité inter-groupes repose sur ``user_id`` (stable et immuable, FR-012).
    Le ``username`` est optionnel et ne sert qu'à l'affichage. Les autres champs
    (nom, indicateurs bot/premium/supprimé, dernière connexion) sont exportés.
    """

    user_id: int
    username: str | None = None
    display_name: str = ""
    first_name: str | None = None
    last_name: str | None = None
    is_bot: bool = False
    is_premium: bool = False
    is_deleted: bool = False
    last_seen: str | None = None
    phone: str | None = None
    description: str | None = None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Member) and other.user_id == self.user_id

    def __hash__(self) -> int:
        return hash(self.user_id)

    @property
    def label(self) -> str:
        """``@username`` si présent, sinon le nom affiché, sinon l'identifiant."""
        if self.username:
            return f"@{self.username}"
        return self.display_name or str(self.user_id)


@dataclass
class TargetGroup:
    """Un groupe à analyser (FR-006 à FR-010)."""

    raw_input: str
    identifier: str
    title: str | None = None
    handle: str | None = None
    access_status: AccessStatus = AccessStatus.ERROR
    members: list[Member] = field(default_factory=list)
    error_message: str | None = None
    total_count: int | None = None  # total annoncé par Telegram (peut dépasser les membres lus)

    @property
    def label(self) -> str:
        """Étiquette d'affichage : ``@handle`` si présent, sinon titre, sinon identifiant."""
        if self.handle:
            return f"@{self.handle}"
        return self.title or self.identifier


@dataclass
class AnalysisResult:
    """Résultat du croisement des groupes (FR-013/014).

    ``membership`` mappe chaque ``user_id`` vers l'ensemble des étiquettes de groupes
    où il apparaît. ``single_group`` et ``multi_group`` en dérivent.
    """

    membership: dict[int, set[str]] = field(default_factory=dict)
    single_group: list[tuple[Member, str]] = field(default_factory=list)
    multi_group: list[tuple[Member, list[str]]] = field(default_factory=list)
