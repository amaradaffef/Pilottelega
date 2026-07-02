"""Onglet « Retirer » : retire des membres de groupes (mode masse ou par utilisateur).

Action réelle et sensible : aperçu obligatoire + confirmation avant exécution, rapport
des résultats. Nécessite les droits admin « exclure des utilisateurs » dans les groupes.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
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
from pilottelega.core.removal import (
    Removal,
    RemovalFilter,
    plan_mass_removal,
    plan_user_removal,
)
from pilottelega.core.telegram_service import TelegramService

logger = get_logger(__name__)


class RemovalTab(QWidget):
    """Sélection des retraits, aperçu, puis exécution confirmée."""

    # Émis quand la case « Exclure les bots » de cet onglet change (synchronisée globalement).
    excludeBotsChanged = Signal(bool)

    def __init__(self, service: TelegramService) -> None:
        super().__init__()
        self.service = service
        self.groups: list[TargetGroup] = []
        self._filter = RemovalFilter()
        self._plan: list[Removal] = []
        self._multi_members: dict[int, tuple[str, list[tuple[str, str]]]] = {}

        layout = QVBoxLayout(self)

        self.admin_note = QLabel()
        self.admin_note.setWordWrap(True)
        self.admin_note.setStyleSheet("color: #ef6c00;")
        layout.addWidget(self.admin_note)

        # Exclure les bots, directement au moment du retrait (piloté/synchronisé globalement).
        self.exclude_bots_check = QCheckBox()
        self.exclude_bots_check.stateChanged.connect(self._on_exclude_bots_toggled)
        layout.addWidget(self.exclude_bots_check)

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

        # Tout cocher / décocher + compteur des lignes actuellement cochées.
        select_row = QHBoxLayout()
        self.select_all_check = QCheckBox()
        self.select_all_check.setChecked(True)
        self.select_all_check.stateChanged.connect(self._toggle_all)
        select_row.addWidget(self.select_all_check)
        select_row.addStretch()
        self.selected_count_label = QLabel()
        self.selected_count_label.setStyleSheet("font-weight: bold;")
        select_row.addWidget(self.selected_count_label)
        layout.addLayout(select_row)

        # Aperçu (colonne 0 = case à cocher pour inclure/exclure la ligne)
        self.table = QTableWidget(0, 3)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # Cocher/décocher une ligne met à jour le compteur en direct.
        self.table.itemChanged.connect(self._on_table_item_changed)
        layout.addWidget(self.table)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.retranslate()
        self._on_mode_changed()

    # ----- Exclusion des bots (synchronisée avec la fenêtre principale) --------------

    def _on_exclude_bots_toggled(self) -> None:
        """Relaie le changement de la case bots vers la fenêtre principale."""
        self.excludeBotsChanged.emit(self.exclude_bots_check.isChecked())

    def set_exclude_bots(self, value: bool) -> None:
        """Met la case bots à ``value`` sans réémettre (synchronisation depuis l'extérieur)."""
        if value == self.exclude_bots_check.isChecked():
            return
        self.exclude_bots_check.blockSignals(True)
        self.exclude_bots_check.setChecked(value)
        self.exclude_bots_check.blockSignals(False)

    # ----- Données ------------------------------------------------------------------

    def update_groups(
        self, groups: list[TargetGroup], filter_: RemovalFilter | None = None
    ) -> None:
        """Recharge les groupes et les membres multi-groupes (candidats au retrait).

        ``filter_`` exclut les comptes protégés et (si activé) les bots des candidats.
        """
        self.groups = groups
        self._filter = filter_ or RemovalFilter()
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
                if self._filter.is_excluded(member):
                    continue
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
            self._plan = plan_mass_removal(self.groups, keep, self._filter) if keep else []
        else:
            user_id = self.user_combo.currentData()
            remove_identifiers = [
                self.user_groups_list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.user_groups_list.count())
                if self.user_groups_list.item(i).checkState() == Qt.CheckState.Checked
            ]
            self._plan = (
                plan_user_removal(self.groups, user_id, remove_identifiers, self._filter)
                if user_id is not None
                else []
            )

        self.table.blockSignals(True)
        self.table.setRowCount(len(self._plan))
        for row, removal in enumerate(self._plan):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check.setCheckState(Qt.CheckState.Checked)
            self.table.setItem(row, 0, check)
            self.table.setItem(row, 1, QTableWidgetItem(removal.user_label))
            self.table.setItem(row, 2, QTableWidgetItem(removal.group_label))
        self.table.blockSignals(False)

        self.select_all_check.blockSignals(True)
        self.select_all_check.setChecked(True)
        self.select_all_check.blockSignals(False)
        self._update_selected_count()
        self.execute_btn.setEnabled(bool(self._plan))
        self.status.setText("" if self._plan else tr("removal.empty"))

    def _toggle_all(self) -> None:
        """Coche ou décoche toutes les lignes de l'aperçu."""
        state = (
            Qt.CheckState.Checked if self.select_all_check.isChecked() else Qt.CheckState.Unchecked
        )
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None:
                item.setCheckState(state)
        self.table.blockSignals(False)
        self._update_selected_count()

    def _on_table_item_changed(self, item: QTableWidgetItem) -> None:
        """Une case (colonne 0) a changé : rafraîchit le compteur de sélection."""
        if item.column() == 0:
            self._update_selected_count()

    def _update_selected_count(self) -> None:
        """Affiche combien de lignes sont actuellement cochées (à retirer)."""
        count = len(self._selected_removals())
        self.selected_count_label.setText(tr("removal.selected_count", count=count))

    def _selected_removals(self) -> list[Removal]:
        """Retraits dont la case est cochée (dans l'ordre du plan)."""
        return [
            self._plan[row]
            for row in range(self.table.rowCount())
            if self.table.item(row, 0) is not None
            and self.table.item(row, 0).checkState() == Qt.CheckState.Checked
        ]

    @asyncSlot()
    async def on_execute(self) -> None:
        """Confirme puis exécute les retraits cochés, et affiche un rapport."""
        if not self._plan:
            self.status.setText(tr("removal.need_preview"))
            return
        selected = self._selected_removals()
        if not selected:
            self.status.setText(tr("removal.empty"))
            return
        confirm = QMessageBox.question(
            self,
            tr("removal.confirm_title"),
            tr("removal.confirm_body", count=len(selected)),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        ban = self.ban_check.isChecked()
        self.preview_btn.setEnabled(False)
        self.execute_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(selected))
        self.progress.setValue(0)

        def on_progress(done: int, total: int) -> None:
            self.progress.setValue(done)
            self.status.setText(tr("removal.running", done=done, total=total))

        results = await self.service.execute_removals(selected, ban=ban, progress=on_progress)
        ok = sum(1 for r in results if r.ok)
        failed = len(results) - ok
        message = tr("removal.done", ok=ok, failed=failed)
        if failed:
            first = next((r for r in results if not r.ok and r.error), None)
            if first is not None:
                who = f"{first.removal.user_label} (id {first.removal.user_id})"
                message += "\n" + tr("removal.first_error", error=f"{who} — {first.error}")
        self.status.setText(message)

        self.progress.setVisible(False)
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(False)
        self._plan = []
        self.table.setRowCount(0)
        self._update_selected_count()

    def retranslate(self) -> None:
        """Met à jour tous les textes selon la langue courante."""
        self.admin_note.setText("⚠ " + tr("removal.admin_note"))
        self.exclude_bots_check.setText(tr("main.exclude_bots"))
        self.mode_label.setText(tr("removal.mode"))
        self.mode_combo.setItemText(0, tr("removal.mode_mass"))
        self.mode_combo.setItemText(1, tr("removal.mode_user"))
        self.keep_label.setText(tr("removal.keep_group"))
        self.user_label.setText(tr("removal.user"))
        self.remove_hint.setText(tr("removal.remove_hint"))
        self.ban_check.setText(tr("removal.ban"))
        self.preview_btn.setText(tr("removal.preview"))
        self.select_all_check.setText(tr("removal.select_all"))
        self._update_selected_count()
        self.execute_btn.setText(tr("removal.execute"))
        self.table.setHorizontalHeaderLabels(
            ["", tr("removal.col_member"), tr("removal.col_group")]
        )
