"""Fenêtre principale : saisie des liens, récupération des membres, onglets (FR-006/009/016).

Les récupérations sont ``await``-ées via qasync, avec barre de progression : l'UI reste
réactive (Principe III / SC-005). Une ligne invalide n'interrompt pas le lot (FR-007).
Interface traduisible (FR/EN/RU) avec sélecteur de langue.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
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
    QScrollArea,
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
from pilottelega.core.removal import RemovalFilter, parse_protected
from pilottelega.core.telegram_service import TelegramService
from pilottelega.ui.analysis_tab import AnalysisTab
from pilottelega.ui.group_tab import GroupTab
from pilottelega.ui.groups_dialog import GroupsDialog
from pilottelega.ui.history_tab import HistoryTab
from pilottelega.ui.removal_tab import RemovalTab

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Écran principal de l'application après connexion."""

    def __init__(self, service: TelegramService) -> None:
        super().__init__()
        self.service = service
        self.groups: list[TargetGroup] = []
        # Compte connecté : toujours exclu des retraits (on ne peut pas se retirer soi-même).
        self._self_user_id: int | None = None
        self._self_label: str | None = None
        # Taille adaptée à l'écran disponible : jamais plus grande que le bureau utile
        # (sinon le bas de la fenêtre passe sous la barre des tâches — cf. capture utilisateur).
        screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        width, height = 950, 850
        if available is not None:
            width = min(width, available.width() - 40)
            height = min(height, available.height() - 80)
        self.resize(width, height)

        # Menu en haut : gestion des groupes enregistrés (définis une fois pour toutes).
        self._saved_groups: list[str] = preferences.load_groups()
        self.groups_menu = self.menuBar().addMenu("")
        self.manage_groups_action = self.groups_menu.addAction("")
        self.manage_groups_action.triggered.connect(self._open_groups_dialog)

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
        # Pré-remplit avec les groupes enregistrés (plus besoin de les recoller à chaque fois).
        if self._saved_groups:
            self.links_edit.setPlainText("\n".join(self._saved_groups))
        layout.addWidget(self.links_edit)

        self.descr_check = QCheckBox()
        layout.addWidget(self.descr_check)

        self.thorough_check = QCheckBox()
        layout.addWidget(self.thorough_check)

        # « Personnes à ne jamais retirer » : on coche des membres récupérés puis « Ajouter »,
        # ou on saisit/colle directement une liste de comptes (@pseudos / IDs).
        self._protected_persons: list[str] = preferences.load_protected_persons()
        self.protected_label = QLabel()
        layout.addWidget(self.protected_label)
        # Saisie manuelle directe d'une liste de comptes à protéger.
        manual_row = QHBoxLayout()
        self.protected_input = QLineEdit()
        self.protected_input.returnPressed.connect(self._on_add_manual_protected)
        manual_row.addWidget(self.protected_input)
        self.protected_add_manual_btn = QPushButton()
        self.protected_add_manual_btn.clicked.connect(self._on_add_manual_protected)
        manual_row.addWidget(self.protected_add_manual_btn)
        layout.addLayout(manual_row)
        protected_row = QHBoxLayout()
        # Gauche : filtre + liste cochable des membres + bouton « Ajouter les cochés ».
        picker_col = QVBoxLayout()
        self.member_search = QLineEdit()
        self.member_search.textChanged.connect(self._populate_member_picker)
        picker_col.addWidget(self.member_search)
        self.member_picker = QListWidget()
        self.member_picker.setMinimumHeight(180)
        picker_col.addWidget(self.member_picker)
        self.protected_add_btn = QPushButton()
        self.protected_add_btn.clicked.connect(self._on_add_checked_members)
        picker_col.addWidget(self.protected_add_btn)
        protected_row.addLayout(picker_col)
        # Droite : liste des personnes exclues + bouton « Retirer la sélection ».
        excluded_col = QVBoxLayout()
        self.protected_list = QListWidget()
        self.protected_list.setMinimumHeight(180)
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
        self.tabs.setMinimumHeight(320)
        layout.addWidget(self.tabs)

        self.analysis_tab = AnalysisTab()
        self.tabs.addTab(self.analysis_tab, tr("main.analysis_tab"))
        self.removal_tab = RemovalTab(service)
        # La case « Exclure les bots » de l'onglet Suppression pilote le réglage global.
        self.removal_tab.excludeBotsChanged.connect(self._on_removal_exclude_bots)
        self.removal_tab.set_exclude_bots(self.exclude_bots_check.isChecked())
        # Après un retrait, re-scanner les groupes concernés pour afficher la liste à jour.
        self.removal_tab.groupsRescanRequested.connect(self._rescan_groups)
        self.tabs.addTab(self.removal_tab, tr("main.removal_tab"))

        # Onglet Historique : rafraîchi après chaque exécution de retrait.
        self.history_tab = HistoryTab()
        self.removal_tab.historyChanged.connect(self.history_tab.reload)
        self.tabs.addTab(self.history_tab, tr("main.history_tab"))

        # Zone défilable : si le contenu dépasse la hauteur de l'écran, une barre de
        # défilement apparaît au lieu de rejeter les champs sous la barre des tâches.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(central)
        self.setCentralWidget(scroll)
        self.retranslate()

    def retranslate(self) -> None:
        """Met à jour tous les textes (fenêtre + onglets) selon la langue courante."""
        self.setWindowTitle(tr("app.title"))
        self.groups_menu.setTitle(tr("menu.groups"))
        self.manage_groups_action.setText(tr("menu.manage_groups"))
        self.lang_label.setText(tr("common.language"))
        self.links_label.setText(tr("main.links_label"))
        self.descr_check.setText(tr("main.fetch_descriptions"))
        self.thorough_check.setText(tr("main.thorough"))
        self.protected_label.setText(tr("main.protected_label"))
        self.protected_input.setPlaceholderText(tr("main.protected_input_placeholder"))
        self.protected_add_manual_btn.setText(tr("main.protected_add_manual"))
        self.member_search.setPlaceholderText(tr("main.protected_search"))
        self.protected_add_btn.setText(tr("main.protected_add"))
        self.protected_remove_btn.setText(tr("main.protected_remove"))
        self.exclude_bots_check.setText(tr("main.exclude_bots"))
        self.fetch_btn.setText(tr("main.fetch"))
        self.tabs.setTabText(self.tabs.indexOf(self.analysis_tab), tr("main.analysis_tab"))
        self.tabs.setTabText(self.tabs.indexOf(self.removal_tab), tr("main.removal_tab"))
        self.tabs.setTabText(self.tabs.indexOf(self.history_tab), tr("main.history_tab"))
        for index in range(self.tabs.count()):
            widget = self.tabs.widget(index)
            if hasattr(widget, "retranslate"):
                widget.retranslate()

    def _open_groups_dialog(self) -> None:
        """Ouvre la popup de gestion des groupes ; enregistre et pré-remplit les liens."""
        dialog = GroupsDialog(self._saved_groups, self)
        if dialog.exec():
            self._saved_groups = dialog.groups()
            preferences.save_groups(self._saved_groups)
            self.links_edit.setPlainText("\n".join(self._saved_groups))

    def on_language_changed(self) -> None:
        """Applique et mémorise la langue, puis retraduit l'interface."""
        code = self.lang_combo.currentData()
        i18n.set_language(code)
        preferences.save_language(code)
        self.retranslate()

    def _current_filter(self) -> RemovalFilter:
        """Construit la politique : personnes protégées (@pseudo/ID) + bots + compte connecté."""
        return RemovalFilter.from_raw(
            "\n".join(self._protected_persons),
            exclude_bots=self.exclude_bots_check.isChecked(),
            self_user_id=self._self_user_id,
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

    def _on_add_manual_protected(self) -> None:
        """Ajoute à la liste protégée les comptes saisis/collés (@pseudos / IDs / liens).

        Accepte plusieurs comptes séparés par des virgules, espaces ou retours ligne.
        Chaque compte est normalisé en ``@pseudo`` ou en identifiant numérique.
        """
        raw = self.protected_input.text().strip()
        if not raw:
            return
        ids, usernames = parse_protected(raw)
        tokens = [f"@{name}" for name in sorted(usernames)] + [str(i) for i in sorted(ids)]
        existing = {p.lower() for p in self._protected_persons}
        added = False
        for token in tokens:
            if token.lower() in existing:
                continue
            self._protected_persons.append(token)
            self.protected_list.addItem(token)
            existing.add(token.lower())
            added = True
        if added:
            self.protected_input.clear()
            self._save_protected_persons()

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
        self.removal_tab.set_self_account(self._self_label)
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

        # Mémorise les liens saisis pour les retrouver au prochain lancement.
        lines = [ln.strip() for ln in self.links_edit.toPlainText().splitlines() if ln.strip()]
        if lines != self._saved_groups:
            self._saved_groups = lines
            preferences.save_groups(lines)

        # Identifie le compte connecté (pour ne jamais se retirer soi-même).
        if self._self_user_id is None:
            me = await self.service.get_me()
            if me is not None:
                self._self_user_id = getattr(me, "id", None)
                uname = getattr(me, "username", None)
                first = getattr(me, "first_name", None)
                self._self_label = f"@{uname}" if uname else (first or str(self._self_user_id))

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

    @asyncSlot(list)
    async def _rescan_groups(self, identifiers: list[str]) -> None:
        """Re-récupère les groupes indiqués (après un retrait) et rafraîchit les vues.

        Permet d'afficher la liste des membres **après** suppression, sans action manuelle.
        Reprend les options de récupération courantes (descriptions / mode complet).
        """
        if not identifiers:
            return
        fetch_descriptions = self.descr_check.isChecked()
        thorough = self.thorough_check.isChecked()
        self.status.setText(tr("main.rescan_running"))
        for identifier in identifiers:
            group = await self.service.fetch_group(
                identifier, fetch_descriptions=fetch_descriptions, thorough=thorough
            )
            self._add_group_tab(group)
        self._refresh_views()
        self.status.setText(tr("main.rescan_done", count=len(identifiers)))

    def _add_group_tab(self, group: TargetGroup) -> None:
        """Ajoute (ou remplace) l'onglet d'un groupe et mémorise ses données.

        Un nouveau scan du même groupe **rafraîchit** son onglet au lieu d'en créer un
        doublon : on retire tout onglet existant portant le même identifiant avant d'insérer.
        """
        self.groups = [g for g in self.groups if g.identifier != group.identifier]
        self.groups.append(group)
        # Retire les onglets déjà présents pour ce groupe (évite les doublons au re-scan).
        index = 0
        while index < self.tabs.count():
            widget = self.tabs.widget(index)
            if isinstance(widget, GroupTab) and widget.group.identifier == group.identifier:
                self.tabs.removeTab(index)
                widget.deleteLater()
            else:
                index += 1
        # Insère l'onglet du groupe avant les onglets fixes Analyse/Retirer.
        tab = GroupTab(group, exclude_bots=self.exclude_bots_check.isChecked())
        tab.removeRequested.connect(lambda t=tab: self._remove_group_tab(t))
        self.tabs.insertTab(self.tabs.indexOf(self.analysis_tab), tab, group.label)

    def _remove_group_tab(self, tab: GroupTab) -> None:
        """Retire un groupe de l'interface uniquement (jamais de Telegram) et recalcule.

        Le groupe disparaît des onglets, de l'analyse et du retrait ; il pourra être
        récupéré à nouveau via « Récupérer les membres » pour le ré-analyser.
        """
        index = self.tabs.indexOf(tab)
        if index < 0:
            return
        self.groups = [g for g in self.groups if g.identifier != tab.group.identifier]
        self.tabs.removeTab(index)
        tab.deleteLater()
        self._refresh_views()
