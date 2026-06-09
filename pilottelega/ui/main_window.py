"""Fenêtre principale : saisie des liens, récupération des membres, onglets (FR-006/009/016).

Les récupérations sont ``await``-ées via qasync, avec barre de progression : l'UI reste
réactive (Principe III / SC-005). Une ligne invalide n'interrompt pas le lot (FR-007).
Interface traduisible (FR/EN/RU) avec sélecteur de langue.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
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
from pilottelega.core.telegram_service import TelegramService
from pilottelega.ui.analysis_tab import AnalysisTab
from pilottelega.ui.group_tab import GroupTab

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

        self.setCentralWidget(central)
        self.retranslate()

    def retranslate(self) -> None:
        """Met à jour tous les textes (fenêtre + onglets) selon la langue courante."""
        self.setWindowTitle(tr("app.title"))
        self.lang_label.setText(tr("common.language"))
        self.links_label.setText(tr("main.links_label"))
        self.fetch_btn.setText(tr("main.fetch"))
        self.tabs.setTabText(self.tabs.indexOf(self.analysis_tab), tr("main.analysis_tab"))
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

        for index, identifier in enumerate(valid, start=1):
            self.status.setText(tr("main.fetching", id=identifier))
            group = await self.service.fetch_group(identifier)
            self._add_group_tab(group)
            self.progress.setValue(index)

        self.analysis_tab.update_groups(self.groups)

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
        self.tabs.insertTab(self.tabs.count() - 1, GroupTab(group), group.label)
