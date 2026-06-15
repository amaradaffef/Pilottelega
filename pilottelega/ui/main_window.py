"""Fenêtre principale : saisie des liens, récupération des membres, onglets (FR-006/009/016).

Les récupérations sont ``await``-ées via qasync, avec barre de progression : l'UI reste
réactive (Principe III / SC-005). Une ligne invalide n'interrompt pas le lot (FR-007).
Interface traduisible (FR/EN/RU) avec sélecteur de langue.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from pilottelega.app import i18n, preferences
from pilottelega.app.i18n import tr
from pilottelega.app.logging_conf import get_logger
from pilottelega.core.link_parser import parse_links
from pilottelega.core.models import TargetGroup
from pilottelega.core.removal import RemovalFilter
from pilottelega.core.telegram_service import TelegramService
from pilottelega.ui.analysis_tab import AnalysisTab
from pilottelega.ui.group_tab import GroupTab
from pilottelega.ui.removal_tab import RemovalTab

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Écran principal de l'application après connexion."""

    def __init__(self, service: TelegramService) -> None:
        super().__init__()
        self.service = service
        self.groups: list[TargetGroup] = []
        self.resize(900, 600)

        central = QWidget()
        layout = QVBoxLayout(central)

        # Barre supérieure : sélecteur de langue
        top_row = QHBoxLayout()
        top_row.addStretch()
        self.lang_label = QLabel()
        top_row.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        for code, name in i18n.AVAILABLE_LANGUAGES.items():
            self.lang_combo.addItem(name, code)
        self.lang_combo.setCurrentIndex(self.lang_combo.findData(i18n.get_language()))
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        top_row.addWidget(self.lang_combo)
        layout.addLayout(top_row)

        self.links_label = QLabel()
        layout.addWidget(self.links_label)
        self.links_edit = QPlainTextEdit()
        self.links_edit.setPlaceholderText("@groupe1\nt.me/groupe2\nhttps://t.me/groupe3")
        self.links_edit.setMaximumHeight(120)
        layout.addWidget(self.links_edit)

        self.descr_check = QCheckBox()
        layout.addWidget(self.descr_check)

        self.thorough_check = QCheckBox()
        layout.addWidget(self.thorough_check)

        # « Personnes à ne jamais retirer » : on coche des membres récupérés puis « Ajouter ».
        self._protected_persons: list[str] = preferences.load_protected_persons()
        self.protected_label = QLabel()
        layout.addWidget(self.protected_label)
        protected_row = QHBoxLayout()
        # Gauche : filtre + liste cochable des membres + bouton « Ajouter les cochés ».
        picker_col = QVBoxLayout()
        self.member_search = QLineEdit()
        self.member_search.textChanged.connect(self._populate_member_picker)
        picker_col.addWidget(self.member_search)
        self.member_picker = QListWidget()
        self.member_picker.setMaximumHeight(300)
        picker_col.addWidget(self.member_picker)
        self.protected_add_btn = QPushButton()
        self.protected_add_btn.clicked.connect(self._on_add_checked_members)
        picker_col.addWidget(self.protected_add_btn)
        protected_row.addLayout(picker_col)
        # Droite : liste des personnes exclues + bouton « Retirer la sélection ».
        excluded_col = QVBoxLayout()
        self.protected_list = QListWidget()
        self.protected_list.setMaximumHeight(260)
        self.protected_list.addItems(self._protected_persons)
        excluded_col.addWidget(self.protected_list)
        self.protected_remove_btn = QPushButton()
        self.protected_remove_btn.clicked.connect(self._on_remove_protected_person)
        excluded_col.addWidget(self.protected_remove_btn)
        protected_row.addLayout(excluded_col)
        layout.addLayout(protected_row)

        # Exclusion des bots (gouverne aussi l'analyse et les listes).
        self.exclude_bots_check = QCheckBox()
        self.exclude_bots_check.setChecked(preferences.load_exclude_bots())
        self.exclude_bots_check.stateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.exclude_bots_check)

        self.fetch_btn = QPushButton()
        self.fetch_btn.clicked.connect(self.on_fetch)
        layout.addWidget(self.fetch_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.analysis_tab = AnalysisTab()
        self.tabs.addTab(self.analysis_tab, tr("main.analysis_tab"))
        self.removal_tab = RemovalTab(service)
        # La case « Exclure les bots » de l'onglet Suppression pilote le réglage global.
        self.removal_tab.excludeBotsChanged.connect(self._on_removal_exclude_bots)
        self.removal_tab.set_exclude_bots(self.exclude_bots_check.isChecked())
        self.tabs.addTab(self.removal_tab, tr("main.removal_tab"))

        self.setCentralWidget(central)
        self.retranslate()

    def retranslate(self) -> None:
        """Met à jour tous les textes (fenêtre + onglets) selon la langue courante."""
        self.setWindowTitle(tr("app.title"))
        self.lang_label.setText(tr("common.language"))
        self.links_label.setText(tr("main.links_label"))
        self.descr_check.setText(tr("main.fetch_descriptions"))
        self.thorough_check.setText(tr("main.thorough"))
        self.protected_label.setText(tr("main.protected_label"))
        self.member_search.setPlaceholderText(tr("main.protected_search"))
        self.protected_add_btn.setText(tr("main.protected_add"))
        self.protected_remove_btn.setText(tr("main.protected_remove"))
        self.exclude_bots_check.setText(tr("main.exclude_bots"))
        self.fetch_btn.setText(tr("main.fetch"))
        self.tabs.setTabText(self.tabs.indexOf(self.analysis_tab), tr("main.analysis_tab"))
        self.tabs.setTabText(self.tabs.indexOf(self.removal_tab), tr("main.removal_tab"))
        for index in range(self.tabs.count()):
            widget = self.tabs.widget(index)
            if hasattr(widget, "retranslate"):
                widget.retranslate()

    def on_language_changed(self) -> None:
        """Applique et mémorise la langue, puis retraduit l'interface."""
        code = self.lang_combo.currentData()
        i18n.set_language(code)
        preferences.save_language(code)
        self.retranslate()

    def _current_filter(self) -> RemovalFilter:
        """Construit la politique : personnes protégées (@pseudo/ID) + exclusion des bots."""
        return RemovalFilter.from_raw(
            "\n".join(self._protected_persons),
            exclude_bots=self.exclude_bots_check.isChecked(),
        )

    @staticmethod
    def _member_token(member: object) -> str:
        """Jeton stable et parsable pour un membre : ``@username`` sinon son identifiant."""
        username = getattr(member, "username", None)
        return f"@{username}" if username else str(getattr(member, "user_id", ""))

    def _populate_member_picker(self) -> None:
        """Remplit la liste cochable des membres récupérés (filtrée, sans déjà-exclus/bots)."""
        query = self.member_search.text().strip().lower()
        exclude_bots = self.exclude_bots_check.isChecked()
        protected = {p.lower() for p in self._protected_persons}
        seen: set[int] = set()
        self.member_picker.blockSignals(True)
        self.member_picker.clear()
        for group in self.groups:
            for member in group.members:
                if member.user_id in seen:
                    continue
                seen.add(member.user_id)
                if exclude_bots and member.is_bot:
                    continue
                token = self._member_token(member)
                if token.lower() in protected:
                    continue
                haystack = f"{member.label} {member.username or ''} {member.user_id}".lower()
                if query and query not in haystack:
                    continue
                item = QListWidgetItem(member.label)
                item.setData(Qt.ItemDataRole.UserRole, token)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.member_picker.addItem(item)
        self.member_picker.blockSignals(False)

    def _on_add_checked_members(self) -> None:
        """Ajoute les membres cochés à la liste des personnes à ne jamais retirer."""
        existing = {p.lower() for p in self._protected_persons}
        added = False
        for i in range(self.member_picker.count()):
            item = self.member_picker.item(i)
            if item.checkState() != Qt.CheckState.Checked:
                continue
            token = str(item.data(Qt.ItemDataRole.UserRole))
            if token.lower() in existing:
                continue
            self._protected_persons.append(token)
            self.protected_list.addItem(token)
            existing.add(token.lower())
            added = True
        if added:
            self._save_protected_persons()
        else:
            self._populate_member_picker()  # décoche au moins l'affichage

    def _on_remove_protected_person(self) -> None:
        """Retire de la liste la personne protégée sélectionnée."""
        row = self.protected_list.currentRow()
        if row < 0:
            return
        self.protected_list.takeItem(row)
        del self._protected_persons[row]
        self._save_protected_persons()

    def _save_protected_persons(self) -> None:
        """Mémorise la liste des personnes protégées et recalcule les vues."""
        preferences.save_protected_persons(self._protected_persons)
        if self.groups:
            self._refresh_views()  # repeuple aussi le sélecteur de membres
        else:
            self._populate_member_picker()

    def _refresh_views(self) -> None:
        """Réapplique le filtre courant aux onglets de groupe, à l'analyse et au retrait."""
        filter_ = self._current_filter()
        self._populate_member_picker()
        for index in range(self.tabs.count()):
            widget = self.tabs.widget(index)
            if isinstance(widget, GroupTab):
                widget.set_exclude_bots(filter_.exclude_bots)
        self.removal_tab.set_exclude_bots(filter_.exclude_bots)
        self.analysis_tab.update_groups(self.groups, exclude_bots=filter_.exclude_bots)
        self.removal_tab.update_groups(self.groups, filter_)

    def _on_removal_exclude_bots(self, value: bool) -> None:
        """La case bots de l'onglet Suppression a changé : pilote le réglage global."""
        # Met à jour la case principale (déclenche on_filter_changed → sauvegarde + refresh).
        self.exclude_bots_check.setChecked(value)

    def on_filter_changed(self) -> None:
        """Mémorise l'option bots et recalcule les vues (sans re-récupérer)."""
        preferences.save_exclude_bots(self.exclude_bots_check.isChecked())
        if self.groups:
            self._refresh_views()

    @asyncSlot()
    async def on_fetch(self) -> None:
        """Normalise les liens, récupère chaque groupe et met à jour les onglets."""
        valid, invalid = parse_links(self.links_edit.toPlainText())
        if not valid:
            self.status.setText(tr("main.no_valid_links"))
            return

        self.fetch_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(valid))
        self.progress.setValue(0)

        fetch_descriptions = self.descr_check.isChecked()
        thorough = self.thorough_check.isChecked()
        for index, identifier in enumerate(valid, start=1):
            self.status.setText(tr("main.fetching", id=identifier))
            group = await self.service.fetch_group(
                identifier, fetch_descriptions=fetch_descriptions, thorough=thorough
            )
            self._add_group_tab(group)
            self.progress.setValue(index)

        self._refresh_views()

        message = tr("main.fetched_summary", count=len(valid))
        if invalid:
            message += tr("main.ignored_lines", count=len(invalid), lines=", ".join(invalid))
        self.status.setText(message)
        self.progress.setVisible(False)
        self.fetch_btn.setEnabled(True)

    def _add_group_tab(self, group: TargetGroup) -> None:
        """Ajoute (ou remplace) l'onglet d'un groupe et mémorise ses données."""
        self.groups = [g for g in self.groups if g.identifier != group.identifier]
        self.groups.append(group)
        # Insère l'onglet du groupe avant les onglets fixes Analyse/Retirer.
        tab = GroupTab(group, exclude_bots=self.exclude_bots_check.isChecked())
        self.tabs.insertTab(self.tabs.indexOf(self.analysis_tab), tab, group.label)
