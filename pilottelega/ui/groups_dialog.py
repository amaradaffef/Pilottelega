"""Fenêtre popup de gestion de la liste des groupes enregistrés.

Permet d'ajouter/supprimer les liens de groupes une fois pour toutes ; la liste est
persistée par l'appelant (:mod:`pilottelega.app.preferences`).
"""

from __future__ import annotations

import re

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)

from pilottelega.app.i18n import tr

# Séparateurs acceptés lors d'un collage multiple (virgule, point-virgule, espaces, sauts).
_SPLIT = re.compile(r"[\s,;]+")


class GroupsDialog(QDialog):
    """Édite la liste des liens de groupes (ajout/suppression)."""

    def __init__(self, groups: list[str], parent: object | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.intro = QLabel()
        self.intro.setWordWrap(True)
        layout.addWidget(self.intro)

        add_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.returnPressed.connect(self._on_add)
        add_row.addWidget(self.input)
        self.add_btn = QPushButton()
        self.add_btn.clicked.connect(self._on_add)
        add_row.addWidget(self.add_btn)
        layout.addLayout(add_row)

        self.list = QListWidget()
        self.list.addItems(groups)
        self.list.setMinimumSize(420, 240)
        layout.addWidget(self.list)

        self.remove_btn = QPushButton()
        self.remove_btn.clicked.connect(self._on_remove)
        layout.addWidget(self.remove_btn)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.retranslate()

    def _on_add(self) -> None:
        """Ajoute le(s) groupe(s) saisi(s) (plusieurs acceptés d'un coup), en dédupliquant."""
        existing = {self.list.item(i).text() for i in range(self.list.count())}
        added = False
        for token in _SPLIT.split(self.input.text().strip()):
            if token and token not in existing:
                self.list.addItem(token)
                existing.add(token)
                added = True
        if added:
            self.input.clear()

    def _on_remove(self) -> None:
        """Retire les groupes sélectionnés de la liste."""
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))

    def groups(self) -> list[str]:
        """Retourne la liste courante des liens de groupes."""
        return [self.list.item(i).text() for i in range(self.list.count())]

    def retranslate(self) -> None:
        """Met à jour les textes selon la langue courante."""
        self.setWindowTitle(tr("groups_dialog.title"))
        self.intro.setText(tr("groups_dialog.intro"))
        self.input.setPlaceholderText(tr("groups_dialog.input_placeholder"))
        self.add_btn.setText(tr("groups_dialog.add"))
        self.remove_btn.setText(tr("groups_dialog.remove"))
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("groups_dialog.save"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(
            tr("groups_dialog.cancel")
        )
