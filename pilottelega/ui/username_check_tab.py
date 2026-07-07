"""Onglet « Vérification de comptes » : résout une liste de @username et rapporte l'état.

Pour chaque compte : existe ou non, type (utilisateur/bot/canal/groupe) et s'il est supprimé.
Chaque vérification = une requête réseau ; gestion anti-flood (pause + nouvelle tentative).
"""

from __future__ import annotations

import re

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from pilottelega.app.i18n import tr
from pilottelega.core.telegram_service import TelegramService, UsernameCheck

# Séparateurs acceptés dans la saisie (virgule, point-virgule, espaces, sauts de ligne).
_SPLIT = re.compile(r"[\s,;]+")

_FOUND_COLOR = "#2e7d32"
_MISSING_COLOR = "#c62828"


class UsernameCheckTab(QWidget):
    """Colle une liste de @username, les vérifie et affiche l'état de chacun."""

    def __init__(self, service: TelegramService) -> None:
        super().__init__()
        self.service = service
        layout = QVBoxLayout(self)

        self.hint = QLabel()
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)

        self.input = QPlainTextEdit()
        self.input.setMaximumHeight(120)
        layout.addWidget(self.input)

        self.check_btn = QPushButton()
        self.check_btn.clicked.connect(self.on_check)
        layout.addWidget(self.check_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.table = QTableWidget(0, 5)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.retranslate()

    @asyncSlot()
    async def on_check(self) -> None:
        """Vérifie la liste de comptes saisie et remplit la table."""
        tokens = [t.lstrip("@") for t in _SPLIT.split(self.input.toPlainText().strip()) if t]
        if not tokens:
            self.status.setText(tr("username.empty"))
            return

        self.check_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(tokens))
        self.progress.setValue(0)

        def on_progress(done: int, total: int) -> None:
            self.progress.setValue(done)
            self.status.setText(tr("username.running", done=done, total=total))

        def on_wait(seconds: int, done: int, total: int) -> None:
            self.status.setText(tr("username.flood_wait", seconds=seconds, done=done, total=total))

        results = await self.service.check_usernames(
            tokens, progress=on_progress, delay=0.5, on_wait=on_wait
        )
        self._fill(results)

        found = sum(1 for r in results if r.found)
        self.status.setText(tr("username.done", found=found, missing=len(results) - found))
        self.progress.setVisible(False)
        self.check_btn.setEnabled(True)

    def _fill(self, results: list[UsernameCheck]) -> None:
        self.table.setRowCount(len(results))
        for row, res in enumerate(results):
            status = tr("username.found") if res.found else tr("username.not_found")
            if res.error:
                status = res.error
            kind = tr(f"username.kind_{res.kind}") if res.found and res.kind else ""
            deleted = tr("common.yes") if res.deleted else ""
            values = [res.username, status, kind, deleted, res.name]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 1:
                    item.setForeground(QColor(_FOUND_COLOR if res.found else _MISSING_COLOR))
                self.table.setItem(row, col, item)

    def retranslate(self) -> None:
        """Met à jour les textes selon la langue courante."""
        self.hint.setText(tr("username.hint"))
        self.input.setPlaceholderText(tr("username.placeholder"))
        self.check_btn.setText(tr("username.check"))
        self.table.setHorizontalHeaderLabels(
            [
                tr("username.col_username"),
                tr("username.col_status"),
                tr("username.col_type"),
                tr("username.col_deleted"),
                tr("username.col_name"),
            ]
        )
