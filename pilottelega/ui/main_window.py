"""Fenêtre principale : saisie des liens, récupération des membres, onglets (FR-006/009/016).

Les récupérations sont ``await``-ées via qasync, avec une barre de progression : l'UI reste
réactive (Principe III / SC-005). Une ligne invalide n'interrompt pas le lot (FR-007).
"""

from __future__ import annotations

from PySide6.QtWidgets import (
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
        self.setWindowTitle("Pilottelega")
        self.resize(900, 600)

        central = QWidget()
        layout = QVBoxLayout(central)

        layout.addWidget(QLabel("Collez les liens de groupes (un par ligne) :"))
        self.links_edit = QPlainTextEdit()
        self.links_edit.setPlaceholderText("@groupe1\nt.me/groupe2\nhttps://t.me/groupe3")
        self.links_edit.setMaximumHeight(120)
        layout.addWidget(self.links_edit)

        self.fetch_btn = QPushButton("Récupérer les membres")
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

        # Onglet Analyse permanent (rafraîchi à chaque récupération).
        self.analysis_tab = AnalysisTab()
        self.tabs.addTab(self.analysis_tab, "Analyse")

        self.setCentralWidget(central)

    @asyncSlot()
    async def on_fetch(self) -> None:
        """Normalise les liens, récupère chaque groupe et met à jour les onglets."""
        valid, invalid = parse_links(self.links_edit.toPlainText())
        if not valid:
            self.status.setText("Aucun lien valide à récupérer.")
            return

        self.fetch_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(valid))
        self.progress.setValue(0)

        for index, identifier in enumerate(valid, start=1):
            self.status.setText(f"Récupération de {identifier}…")
            group = await self.service.fetch_group(identifier)
            self._add_group_tab(group)
            self.progress.setValue(index)

        self._refresh_analysis()

        message = f"{len(valid)} groupe(s) récupéré(s)."
        if invalid:
            message += f" {len(invalid)} ligne(s) ignorée(s) : {', '.join(invalid)}"
        self.status.setText(message)
        self.progress.setVisible(False)
        self.fetch_btn.setEnabled(True)

    def _add_group_tab(self, group: TargetGroup) -> None:
        """Ajoute (ou remplace) l'onglet d'un groupe et mémorise ses données."""
        self.groups = [g for g in self.groups if g.identifier != group.identifier]
        self.groups.append(group)
        # Insère avant l'onglet Analyse (toujours en dernier).
        self.tabs.insertTab(self.tabs.count() - 1, GroupTab(group), group.label)

    def _refresh_analysis(self) -> None:
        """Recalcule et affiche l'analyse de recoupement (FR-013/014)."""
        self.analysis_tab.update_groups(self.groups)
