"""Onglet d'affichage d'un groupe : table des membres + badge de statut + export Excel."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pilottelega.app.i18n import tr
from pilottelega.app.logging_conf import get_logger
from pilottelega.core.export import GROUP_COLUMNS, export_group_to_xlsx, member_row
from pilottelega.core.models import AccessStatus, TargetGroup

logger = get_logger(__name__)

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

        self.badge = QLabel()
        self.badge.setStyleSheet(
            f"color: white; background: {_STATUS_COLORS[group.access_status]};"
            " padding: 4px 8px; border-radius: 4px;"
        )
        layout.addWidget(self.badge)

        self.export_btn = QPushButton()
        self.export_btn.clicked.connect(self.on_export)
        layout.addWidget(self.export_btn)

        self.table = QTableWidget(len(group.members), len(GROUP_COLUMNS))
        self.table.setHorizontalHeaderLabels(GROUP_COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for row, member in enumerate(group.members):
            for col, value in enumerate(member_row(member)):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        layout.addWidget(self.table)

        self.retranslate()

    def _status_text(self) -> str:
        status = tr(f"status.{self.group.access_status.value}")
        fetched = len(self.group.members)
        total = self.group.total_count
        if total is not None and total != fetched:
            text = tr("group.status_summary_total", status=status, fetched=fetched, total=total)
        else:
            text = tr("group.status_summary", status=status, count=fetched)
        if self.group.access_status is AccessStatus.ERROR and self.group.error_message:
            text += f" : {self.group.error_message}"
        return text

    def retranslate(self) -> None:
        """Met à jour les textes selon la langue courante."""
        self.badge.setText(self._status_text())
        self.export_btn.setText(tr("common.export_excel"))
        # Les en-têtes de colonnes sont des noms de champs techniques (non traduits).

    def on_export(self) -> None:
        """Exporte les membres du groupe vers un fichier Excel."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("common.export_excel"),
            f"{self.group.identifier}.xlsx",
            tr("common.excel_filter"),
        )
        if not path:
            return
        try:
            export_group_to_xlsx(self.group, path, tr)
        except Exception as exc:  # noqa: BLE001 - retour utilisateur clair
            logger.warning("Échec export groupe: %s", type(exc).__name__)
            QMessageBox.warning(self, tr("app.title"), tr("export.failed", error=str(exc)))
            return
        QMessageBox.information(self, tr("app.title"), tr("export.done", path=path))
