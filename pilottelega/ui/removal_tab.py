"""Onglet « Retirer » : retire des membres de groupes (mode masse ou par utilisateur).

Action réelle et sensible : aperçu obligatoire + confirmation avant exécution, rapport
des résultats. Nécessite les droits admin « exclure des utilisateurs » dans les groupes.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from pilottelega.app.i18n import tr
from pilottelega.app.logging_conf import get_logger
from pilottelega.core.models import TargetGroup
from pilottelega.core.removal import Removal, plan_mass_removal, plan_user_removal
from pilottelega.core.telegram_service import TelegramService

logger = get_logger(__name__)


class RemovalTab(QWidget):
    """Sélection des retraits, aperçu, puis exécution confirmée."""

    def __init__(self, service: TelegramService) -> None:
        super().__init__()
        self.service = service
        self.groups: list[TargetGroup] = []
        self._plan: list[Removal] = []
        self._multi_members: dict[int, tuple[str, list[tuple[str, str]]]] = {}

        layout = QVBoxLayout(self)

        self.admin_note = QLabel()
        self.admin_note.setWordWrap(True)
        self.admin_note.setStyleSheet("color: #ef6c00;")
        layout.addWidget(self.admin_note)

        # Sélecteur de mode
        mode_row = QHBoxLayout()
        self.mode_label = QLabel()
        mode_row.addWidget(self.mode_label)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("", "mass")
        self.mode_combo.addItem("", "user")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Mode masse : groupe à conserver
        self.mass_widget = QWidget()
        mass_row = QHBoxLayout(self.mass_widget)
        self.keep_label = QLabel()
        mass_row.addWidget(self.keep_label)
        self.keep_combo = QComboBox()
        mass_row.addWidget(self.keep_combo)
        mass_row.addStretch()
        layout.addWidget(self.mass_widget)

        # Mode par utilisateur : choix du membre + groupes à cocher
        self.user_widget = QWidget()
        user_layout = QVBoxLayout(self.user_widget)
        user_row = QHBoxLayout()
        self.user_label = QLabel()
        user_row.addWidget(self.user_label)
        self.user_combo = QComboBox()
        self.user_combo.currentIndexChanged.connect(self._on_user_changed)
        user_row.addWidget(self.user_combo)
        user_row.addStretch()
        user_layout.addLayout(user_row)
        self.remove_hint = QLabel()
        user_layout.addWidget(self.remove_hint)
        self.user_groups_list = QListWidget()
        self.user_groups_list.setMaximumHeight(140)
        user_layout.addWidget(self.user_groups_list)
        layout.addWidget(self.user_widget)

        # Actions
        actions = QHBoxLayout()
        self.ban_check = QCheckBox()
        actions.addWidget(self.ban_check)
        self.preview_btn = QPushButton()
        self.preview_btn.clicked.connect(self.on_preview)
        actions.addWidget(self.preview_btn)
        self.execute_btn = QPushButton()
        self.execute_btn.clicked.connect(self.on_execute)
        self.execute_btn.setEnabled(False)
        actions.addWidget(self.execute_btn)
        actions.addStretch()
        layout.addLayout(actions)

        # Aperçu
        self.table = QTableWidget(0, 2)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.retranslate()
        self._on_mode_changed()

    # ----- Données ------------------------------------------------------------------

    def update_groups(self, groups: list[TargetGroup]) -> None:
        """Recharge les groupes et les membres multi-groupes (candidats au retrait)."""
        self.groups = groups
        self._multi_members = self._compute_multi_members()

        self.keep_combo.clear()
        for group in groups:
            self.keep_combo.addItem(group.label, group.identifier)

        self.user_combo.clear()
        for user_id, (label, _groups) in self._multi_members.items():
            self.user_combo.addItem(label, user_id)
        self._on_user_changed()

    def _compute_multi_members(self) -> dict[int, tuple[str, list[tuple[str, str]]]]:
        membership: dict[int, list[tuple[str, str]]] = {}
        labels: dict[int, str] = {}
        for group in self.groups:
            for member in group.members:
                bucket = membership.setdefault(member.user_id, [])
                if group.identifier not in {gi for gi, _ in bucket}:
                    bucket.append((group.identifier, group.label))
                labels.setdefault(member.user_id, member.label)
        return {
            user_id: (labels[user_id], group_list)
            for user_id, group_list in membership.items()
            if len(group_list) > 1
        }

    # ----- Interaction --------------------------------------------------------------

    def _on_mode_changed(self) -> None:
        mode = self.mode_combo.currentData()
        self.mass_widget.setVisible(mode == "mass")
        self.user_widget.setVisible(mode == "user")

    def _on_user_changed(self) -> None:
        self.user_groups_list.clear()
        user_id = self.user_combo.currentData()
        info = self._multi_members.get(user_id) if user_id is not None else None
        if not info:
            return
        _label, group_list = info
        for identifier, group_label in group_list:
            item = QListWidgetItem(group_label)
            item.setData(Qt.ItemDataRole.UserRole, identifier)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.user_groups_list.addItem(item)

    def on_preview(self) -> None:
        """Calcule le plan de retrait selon le mode et l'affiche dans la table."""
        mode = self.mode_combo.currentData()
        if mode == "mass":
            keep = self.keep_combo.currentData()
            self._plan = plan_mass_removal(self.groups, keep) if keep else []
        else:
            user_id = self.user_combo.currentData()
            remove_identifiers = [
                self.user_groups_list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.user_groups_list.count())
                if self.user_groups_list.item(i).checkState() == Qt.CheckState.Checked
            ]
            self._plan = (
                plan_user_removal(self.groups, user_id, remove_identifiers)
                if user_id is not None
                else []
            )

        self.table.setRowCount(len(self._plan))
        for row, removal in enumerate(self._plan):
            self.table.setItem(row, 0, QTableWidgetItem(removal.user_label))
            self.table.setItem(row, 1, QTableWidgetItem(removal.group_label))

        self.execute_btn.setEnabled(bool(self._plan))
        self.status.setText("" if self._plan else tr("removal.empty"))

    @asyncSlot()
    async def on_execute(self) -> None:
        """Confirme puis exécute les retraits, et affiche un rapport."""
        if not self._plan:
            self.status.setText(tr("removal.need_preview"))
            return
        confirm = QMessageBox.question(
            self,
            tr("removal.confirm_title"),
            tr("removal.confirm_body", count=len(self._plan)),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        ban = self.ban_check.isChecked()
        self.preview_btn.setEnabled(False)
        self.execute_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(self._plan))
        self.progress.setValue(0)

        def on_progress(done: int, total: int) -> None:
            self.progress.setValue(done)
            self.status.setText(tr("removal.running", done=done, total=total))

        results = await self.service.execute_removals(self._plan, ban=ban, progress=on_progress)
        ok = sum(1 for r in results if r.ok)
        failed = len(results) - ok
        self.status.setText(tr("removal.done", ok=ok, failed=failed))

        self.progress.setVisible(False)
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(False)
        self._plan = []
        self.table.setRowCount(0)

    def retranslate(self) -> None:
        """Met à jour tous les textes selon la langue courante."""
        self.admin_note.setText("⚠ " + tr("removal.admin_note"))
        self.mode_label.setText(tr("removal.mode"))
        self.mode_combo.setItemText(0, tr("removal.mode_mass"))
        self.mode_combo.setItemText(1, tr("removal.mode_user"))
        self.keep_label.setText(tr("removal.keep_group"))
        self.user_label.setText(tr("removal.user"))
        self.remove_hint.setText(tr("removal.remove_hint"))
        self.ban_check.setText(tr("removal.ban"))
        self.preview_btn.setText(tr("removal.preview"))
        self.execute_btn.setText(tr("removal.execute"))
        self.table.setHorizontalHeaderLabels([tr("removal.col_member"), tr("removal.col_group")])
