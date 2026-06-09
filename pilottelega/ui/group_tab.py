"""Onglet d'affichage d'un groupe : table des membres + badge de statut d'accès (FR-009/010)."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pilottelega.core.models import AccessStatus, TargetGroup

_STATUS_COLORS = {
    AccessStatus.FULL: "#2e7d32",
    AccessStatus.PARTIAL_HIDDEN: "#f9a825",
    AccessStatus.ADMIN_REQUIRED: "#ef6c00",
    AccessStatus.ERROR: "#c62828",
}


class GroupTab(QWidget):
    """Vue d'un ``TargetGroup``."""

    def __init__(self, group: TargetGroup) -> None:
        super().__init__()
        self.group = group
        layout = QVBoxLayout(self)

        badge = QLabel(self._status_text(group))
        badge.setStyleSheet(
            f"color: white; background: {_STATUS_COLORS[group.access_status]};"
            " padding: 4px 8px; border-radius: 4px;"
        )
        layout.addWidget(badge)

        table = QTableWidget(len(group.members), 2)
        table.setHorizontalHeaderLabels(["Membre", "ID"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for row, member in enumerate(group.members):
            table.setItem(row, 0, QTableWidgetItem(member.label))
            table.setItem(row, 1, QTableWidgetItem(str(member.user_id)))
        layout.addWidget(table)

    @staticmethod
    def _status_text(group: TargetGroup) -> str:
        text = f"{group.access_status.label} — {len(group.members)} membre(s)"
        if group.access_status is AccessStatus.ERROR and group.error_message:
            text += f" : {group.error_message}"
        return text
