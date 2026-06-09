"""Onglet Analyse : membres présents dans un seul groupe vs plusieurs (FR-013/014)."""

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

from pilottelega.core.analysis import compute_overlap
from pilottelega.core.models import TargetGroup


def _make_table(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    return table


class AnalysisTab(QWidget):
    """Vue de recoupement, recalculée à la demande via :meth:`update_groups`."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>Présents dans un seul groupe</b>"))
        self.single_table = _make_table(["Membre", "Groupe"])
        layout.addWidget(self.single_table)

        layout.addWidget(QLabel("<b>Présents dans plusieurs groupes</b>"))
        self.multi_table = _make_table(["Membre", "Groupes"])
        layout.addWidget(self.multi_table)

    def update_groups(self, groups: list[TargetGroup]) -> None:
        """Recalcule le recoupement et met à jour les deux tables."""
        result = compute_overlap(groups)

        self.single_table.setRowCount(len(result.single_group))
        for row, (member, group_label) in enumerate(result.single_group):
            self.single_table.setItem(row, 0, QTableWidgetItem(member.label))
            self.single_table.setItem(row, 1, QTableWidgetItem(group_label))

        self.multi_table.setRowCount(len(result.multi_group))
        for row, (member, group_labels) in enumerate(result.multi_group):
            self.multi_table.setItem(row, 0, QTableWidgetItem(member.label))
            self.multi_table.setItem(row, 1, QTableWidgetItem(", ".join(group_labels)))
