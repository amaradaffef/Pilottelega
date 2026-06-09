"""Onglet Analyse : membres dans un seul groupe vs plusieurs + export Excel (FR-013/014)."""

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
from pilottelega.core.analysis import compute_overlap
from pilottelega.core.export import export_analysis_to_xlsx
from pilottelega.core.models import AnalysisResult, TargetGroup

logger = get_logger(__name__)


def _make_table() -> QTableWidget:
    table = QTableWidget(0, 2)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    return table


class AnalysisTab(QWidget):
    """Vue de recoupement, recalculée à la demande via :meth:`update_groups`."""

    def __init__(self) -> None:
        super().__init__()
        self._result = AnalysisResult()
        layout = QVBoxLayout(self)

        self.export_btn = QPushButton()
        self.export_btn.clicked.connect(self.on_export)
        layout.addWidget(self.export_btn)

        self.single_label = QLabel()
        layout.addWidget(self.single_label)
        self.single_table = _make_table()
        layout.addWidget(self.single_table)

        self.multi_label = QLabel()
        layout.addWidget(self.multi_label)
        self.multi_table = _make_table()
        layout.addWidget(self.multi_table)

        self.retranslate()

    def update_groups(self, groups: list[TargetGroup]) -> None:
        """Recalcule le recoupement et met à jour les deux tables."""
        self._result = compute_overlap(groups)
        self._populate()

    def _populate(self) -> None:
        result = self._result
        self.single_table.setRowCount(len(result.single_group))
        for row, (member, group_label) in enumerate(result.single_group):
            self.single_table.setItem(row, 0, QTableWidgetItem(member.label))
            self.single_table.setItem(row, 1, QTableWidgetItem(group_label))

        self.multi_table.setRowCount(len(result.multi_group))
        for row, (member, group_labels) in enumerate(result.multi_group):
            self.multi_table.setItem(row, 0, QTableWidgetItem(member.label))
            self.multi_table.setItem(row, 1, QTableWidgetItem(", ".join(group_labels)))

    def retranslate(self) -> None:
        """Met à jour les textes selon la langue courante."""
        self.export_btn.setText(tr("common.export_excel"))
        self.single_label.setText(f"<b>{tr('analysis.single_title')}</b>")
        self.multi_label.setText(f"<b>{tr('analysis.multi_title')}</b>")
        self.single_table.setHorizontalHeaderLabels(
            [tr("analysis.member_col"), tr("analysis.group_col")]
        )
        self.multi_table.setHorizontalHeaderLabels(
            [tr("analysis.member_col"), tr("analysis.groups_col")]
        )

    def on_export(self) -> None:
        """Exporte l'analyse de recoupement vers un fichier Excel à deux onglets."""
        path, _ = QFileDialog.getSaveFileName(
            self, tr("common.export_excel"), "analyse.xlsx", tr("common.excel_filter")
        )
        if not path:
            return
        try:
            export_analysis_to_xlsx(self._result, path, tr)
        except Exception as exc:  # noqa: BLE001 - retour utilisateur clair
            logger.warning("Échec export analyse: %s", type(exc).__name__)
            QMessageBox.warning(self, tr("app.title"), tr("export.failed", error=str(exc)))
            return
        QMessageBox.information(self, tr("app.title"), tr("export.done", path=path))
