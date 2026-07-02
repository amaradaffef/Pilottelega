"""Onglet « Historique » : liste des retraits effectués (persistant, local).

Alimenté après chaque exécution de retrait ; les données sont lues/écrites via
:mod:`pilottelega.app.history_store`. Un bouton permet de vider l'historique.
"""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pilottelega.app import history_store
from pilottelega.app.i18n import tr
from pilottelega.core.history import ACTION_BAN, RemovalRecord

_OK_COLOR = "#2e7d32"
_FAIL_COLOR = "#c62828"


class HistoryTab(QWidget):
    """Affiche l'historique des retraits (le plus récent en haut)."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self.count_label = QLabel()
        top_row.addWidget(self.count_label)
        top_row.addStretch()
        self.clear_btn = QPushButton()
        self.clear_btn.clicked.connect(self._on_clear)
        top_row.addWidget(self.clear_btn)
        layout.addLayout(top_row)

        self.table = QTableWidget(0, 5)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.reload()
        self.retranslate()

    def reload(self) -> None:
        """Recharge l'historique depuis le stockage local (le plus récent en premier)."""
        records = list(reversed(history_store.load_history()))
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self._fill_row(row, record)
        self.count_label.setText(tr("history.count", count=len(records)))

    def _fill_row(self, row: int, record: RemovalRecord) -> None:
        when = record.timestamp.replace("T", " ")
        action = (
            tr("history.action_ban") if record.action == ACTION_BAN else tr("history.action_kick")
        )
        if record.ok:
            result = tr("history.result_ok")
        else:
            result = tr("history.result_failed", error=record.error or "")
        values = [when, record.user_label, record.group_label, action, result]
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            if col == 4:
                item.setForeground(QColor(_OK_COLOR if record.ok else _FAIL_COLOR))
            self.table.setItem(row, col, item)

    def _on_clear(self) -> None:
        """Demande confirmation puis vide l'historique."""
        confirm = QMessageBox.question(self, tr("history.clear_title"), tr("history.clear_body"))
        if confirm != QMessageBox.StandardButton.Yes:
            return
        history_store.clear_history()
        self.reload()

    def retranslate(self) -> None:
        """Met à jour les textes selon la langue courante."""
        self.clear_btn.setText(tr("history.clear"))
        self.table.setHorizontalHeaderLabels(
            [
                tr("history.col_date"),
                tr("history.col_member"),
                tr("history.col_group"),
                tr("history.col_action"),
                tr("history.col_result"),
            ]
        )
        self.reload()
