"""Onglet « Retirer » : retire des membres de groupes (mode masse ou par utilisateur).

Action réelle et sensible : aperçu obligatoire + confirmation avant exécution, rapport
des résultats. Nécessite les droits admin « exclure des utilisateurs » dans les groupes.
"""

from __future__ import annotations

from datetime import datetime

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
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from pilottelega.app import history_store
from pilottelega.app.i18n import tr
from pilottelega.app.logging_conf import get_logger
from pilottelega.core.history import records_from_results
from pilottelega.core.models import TargetGroup
from pilottelega.core.removal import (
    Removal,
    RemovalFilter,
    parse_protected,
    plan_deleted_removal,
    plan_list_removal,
    plan_mass_removal,
    plan_user_removal,
)
from pilottelega.core.telegram_service import TelegramService

logger = get_logger(__name__)


class RemovalTab(QWidget):
    """Sélection des retraits, aperçu, puis exécution confirmée."""

    # Émis quand la case « Exclure les bots » de cet onglet change (synchronisée globalement).
    excludeBotsChanged = Signal(bool)
    # Émis après une exécution : l'historique local a été mis à jour.
    historyChanged = Signal()
    # Émis après une exécution : identifiants des groupes à re-scanner (liste à jour).
    groupsRescanRequested = Signal(list)

    def __init__(self, service: TelegramService) -> None:
        super().__init__()
        self.service = service
        self.groups: list[TargetGroup] = []
        self._filter = RemovalFilter()
        self._plan: list[Removal] = []
        self._multi_members: dict[int, tuple[str, list[tuple[str, str]]]] = {}
        self._self_account: str | None = None

        layout = QVBoxLayout(self)

        self.admin_note = QLabel()
        self.admin_note.setWordWrap(True)
        self.admin_note.setStyleSheet("color: #ef6c00;")
        layout.addWidget(self.admin_note)

        # Rappel : le compte connecté est exclu des retraits (visible uniquement si connu).
        self.self_note = QLabel()
        self.self_note.setWordWrap(True)
        self.self_note.setStyleSheet("color: #1565c0;")
        self.self_note.setVisible(False)
        layout.addWidget(self.self_note)

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
        self.mode_combo.addItem("", "deleted")
        self.mode_combo.addItem("", "list")
        self.mode_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
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
        # Assez large pour afficher le nom complet du groupe (évite « @Klevoe… » tronqué).
        self.keep_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.keep_combo.setMinimumWidth(280)
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
        self.user_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.user_combo.setMinimumWidth(280)
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

        # Mode « comptes supprimés » : groupe à nettoyer des comptes fantômes.
        self.deleted_widget = QWidget()
        deleted_row = QHBoxLayout(self.deleted_widget)
        self.deleted_label = QLabel()
        deleted_row.addWidget(self.deleted_label)
        self.deleted_combo = QComboBox()
        self.deleted_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.deleted_combo.setMinimumWidth(280)
        deleted_row.addWidget(self.deleted_combo)
        deleted_row.addStretch()
        layout.addWidget(self.deleted_widget)

        # Mode « par liste » : coller une liste de comptes (bots…) à retirer d'un groupe.
        self.list_widget = QWidget()
        list_layout = QVBoxLayout(self.list_widget)
        list_top = QHBoxLayout()
        self.list_group_label = QLabel()
        list_top.addWidget(self.list_group_label)
        self.list_combo = QComboBox()
        self.list_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.list_combo.setMinimumWidth(280)
        list_top.addWidget(self.list_combo)
        list_top.addStretch()
        list_layout.addLayout(list_top)
        self.list_hint = QLabel()
        list_layout.addWidget(self.list_hint)
        self.list_input = QPlainTextEdit()
        self.list_input.setMaximumHeight(120)
        list_layout.addWidget(self.list_input)
        layout.addWidget(self.list_widget)

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

        # Traitement par lots (anti-blocage) : N retraits, pause de M minutes, etc.
        batch_row = QHBoxLayout()
        self.batch_check = QCheckBox()
        self.batch_check.setChecked(True)  # activé par défaut pour protéger le compte
        batch_row.addWidget(self.batch_check)
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 1000)
        self.batch_size_spin.setValue(25)
        batch_row.addWidget(self.batch_size_spin)
        self.batch_members_label = QLabel()
        batch_row.addWidget(self.batch_members_label)
        self.batch_pause_spin = QSpinBox()
        self.batch_pause_spin.setRange(0, 120)
        self.batch_pause_spin.setValue(2)
        batch_row.addWidget(self.batch_pause_spin)
        self.batch_minutes_label = QLabel()
        batch_row.addWidget(self.batch_minutes_label)
        batch_row.addStretch()
        layout.addLayout(batch_row)

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

    def set_self_account(self, label: str | None) -> None:
        """Renseigne le compte connecté (exclu des retraits) et affiche le rappel."""
        self._self_account = label
        self._refresh_self_note()

    def _refresh_self_note(self) -> None:
        """Affiche/masque le rappel d'exclusion du compte connecté selon la langue."""
        if self._self_account:
            self.self_note.setText(tr("removal.self_excluded", account=self._self_account))
            self.self_note.setVisible(True)
        else:
            self.self_note.setVisible(False)

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
        self.deleted_combo.clear()
        self.list_combo.clear()
        for group in groups:
            self.keep_combo.addItem(group.label, group.identifier)
            self.deleted_combo.addItem(group.label, group.identifier)
            self.list_combo.addItem(group.label, group.identifier)

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
        self.deleted_widget.setVisible(mode == "deleted")
        self.list_widget.setVisible(mode == "list")

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
        elif mode == "deleted":
            target = self.deleted_combo.currentData()
            self._plan = plan_deleted_removal(self.groups, target, self._filter) if target else []
        elif mode == "list":
            target = self.list_combo.currentData()
            ids, usernames = parse_protected(self.list_input.toPlainText())
            self._plan = (
                plan_list_removal(self.groups, target, ids, usernames, self._filter)
                if target and (ids or usernames)
                else []
            )
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

        def on_wait(seconds: int, done: int, total: int) -> None:
            # Telegram impose une pause anti-flood : on informe l'utilisateur.
            self.status.setText(tr("removal.flood_wait", seconds=seconds, done=done, total=total))

        def on_pause(remaining: int, done: int, total: int) -> None:
            # Pause volontaire entre deux lots (anti-blocage) : décompte visible.
            self.status.setText(
                tr("removal.batch_pause", remaining=remaining, done=done, total=total)
            )

        # Mode par lots (anti-blocage) : N retraits puis pause de M minutes.
        if self.batch_check.isChecked():
            batch_size = self.batch_size_spin.value()
            batch_pause = float(self.batch_pause_spin.value() * 60)
        else:
            batch_size = 0
            batch_pause = 0.0

        # Petit délai entre retraits pour limiter les blocages anti-flood de Telegram.
        results = await self.service.execute_removals(
            selected,
            ban=ban,
            progress=on_progress,
            delay=1.0,
            on_wait=on_wait,
            batch_size=batch_size,
            batch_pause=batch_pause,
            on_pause=on_pause,
        )

        # Consigne l'action dans l'historique local (persistant) puis notifie l'onglet dédié.
        timestamp = datetime.now().isoformat(timespec="seconds")
        history_store.append_records(records_from_results(results, ban, timestamp))
        self.historyChanged.emit()

        # Re-scanne les groupes d'où des membres ont réellement été retirés (liste à jour).
        rescan = sorted({r.removal.group_identifier for r in results if r.ok})
        if rescan:
            self.groupsRescanRequested.emit(rescan)

        ok = sum(1 for r in results if r.ok)
        failed = len(results) - ok
        message = tr("removal.done", ok=ok, failed=failed)
        if failed:
            first = next((r for r in results if not r.ok and r.error), None)
            if first is not None:
                who = f"{first.removal.user_label} (id {first.removal.user_id})"
                message += "\n" + tr("removal.first_error", error=f"{who} — {first.error}")
                hint = self._error_hint(first.error or "")
                if hint:
                    message += "\n➜ " + hint
        self.status.setText(message)

        self.progress.setVisible(False)
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(False)
        self._plan = []
        self.table.setRowCount(0)
        self._update_selected_count()

    @staticmethod
    def _error_hint(error: str) -> str:
        """Traduit une erreur Telegram technique en conseil compréhensible (ou '')."""
        low = error.lower()
        if "write in this chat" in low or "admin" in low or "not enough rights" in low:
            return tr("removal.err_no_admin")
        if "participant id is invalid" in low:
            return tr("removal.err_participant_invalid")
        if "user_not_participant" in low or "not a participant" in low:
            return tr("removal.err_not_member")
        return ""

    def retranslate(self) -> None:
        """Met à jour tous les textes selon la langue courante."""
        self.admin_note.setText("⚠ " + tr("removal.admin_note"))
        self._refresh_self_note()
        self.exclude_bots_check.setText(tr("main.exclude_bots"))
        self.mode_label.setText(tr("removal.mode"))
        self.mode_combo.setItemText(0, tr("removal.mode_mass"))
        self.mode_combo.setItemText(1, tr("removal.mode_user"))
        self.mode_combo.setItemText(2, tr("removal.mode_deleted"))
        self.mode_combo.setItemText(3, tr("removal.mode_list"))
        self.keep_label.setText(tr("removal.keep_group"))
        self.deleted_label.setText(tr("removal.deleted_group"))
        self.list_group_label.setText(tr("removal.list_group"))
        self.list_hint.setText(tr("removal.list_hint"))
        self.list_input.setPlaceholderText(tr("removal.list_placeholder"))
        self.user_label.setText(tr("removal.user"))
        self.remove_hint.setText(tr("removal.remove_hint"))
        self.ban_check.setText(tr("removal.ban"))
        self.batch_check.setText(tr("removal.batch_label"))
        self.batch_members_label.setText(tr("removal.batch_members"))
        self.batch_minutes_label.setText(tr("removal.batch_minutes"))
        self.preview_btn.setText(tr("removal.preview"))
        self.select_all_check.setText(tr("removal.select_all"))
        self._update_selected_count()
        self.execute_btn.setText(tr("removal.execute"))
        self.table.setHorizontalHeaderLabels(
            ["", tr("removal.col_member"), tr("removal.col_group")]
        )
