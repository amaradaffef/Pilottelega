"""Sélecteur des discussions du compte connecté (groupes publics **et privés**).

Un groupe privé n'a pas de ``@pseudo`` : impossible de le désigner par un lien. On liste donc
les discussions de l'utilisateur pour qu'il coche celles à analyser ; l'identifiant retenu est
le ``@pseudo`` si le groupe est public, sinon son ID numérique.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from pilottelega.app.i18n import tr
from pilottelega.core.telegram_service import DialogInfo


class DialogsPickerDialog(QDialog):
    """Coche les discussions à importer dans la liste des groupes à analyser."""

    def __init__(self, dialogs: list[DialogInfo], parent: object | None = None) -> None:
        super().__init__(parent)
        self._dialogs = dialogs
        layout = QVBoxLayout(self)

        self.intro = QLabel()
        self.intro.setWordWrap(True)
        layout.addWidget(self.intro)

        filter_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.textChanged.connect(self._populate)
        filter_row.addWidget(self.search)
        self.private_only = QCheckBox()
        self.private_only.stateChanged.connect(self._populate)
        filter_row.addWidget(self.private_only)
        self.hide_channels = QCheckBox()
        self.hide_channels.stateChanged.connect(self._populate)
        filter_row.addWidget(self.hide_channels)
        layout.addLayout(filter_row)

        self.list = QListWidget()
        self.list.setMinimumSize(520, 320)
        layout.addWidget(self.list)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self._populate()
        self.retranslate()

    def _populate(self) -> None:
        """Remplit la liste cochable selon le texte recherché et les filtres."""
        query = self.search.text().strip().lower()
        checked = self.selected()  # conserve les cases déjà cochées malgré le filtrage
        self.list.clear()
        for info in self._dialogs:
            if self.private_only.isChecked() and not info.is_private:
                continue
            if self.hide_channels.isChecked() and info.is_channel:
                continue
            if query and query not in f"{info.title} {info.identifier}".lower():
                continue
            item = QListWidgetItem(self._item_text(info))
            item.setData(Qt.ItemDataRole.UserRole, info.identifier)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            state = Qt.CheckState.Checked if info.identifier in checked else Qt.CheckState.Unchecked
            item.setCheckState(state)
            self.list.addItem(item)

    @staticmethod
    def _item_text(info: DialogInfo) -> str:
        """Titre + badges (privé/public, canal) + nombre de membres si connu."""
        badges = [tr("dialogs.private") if info.is_private else info.identifier]
        if info.is_channel:
            badges.append(tr("dialogs.channel"))
        if info.members_count is not None:
            badges.append(tr("dialogs.members", count=info.members_count))
        return f"{info.title}  ({' · '.join(badges)})"

    def selected(self) -> list[str]:
        """Identifiants cochés (``@pseudo`` pour les publics, ID pour les privés)."""
        return [
            str(self.list.item(i).data(Qt.ItemDataRole.UserRole))
            for i in range(self.list.count())
            if self.list.item(i).checkState() == Qt.CheckState.Checked
        ]

    def retranslate(self) -> None:
        """Met à jour les textes selon la langue courante."""
        self.setWindowTitle(tr("dialogs.title"))
        self.intro.setText(tr("dialogs.intro"))
        self.search.setPlaceholderText(tr("dialogs.search"))
        self.private_only.setText(tr("dialogs.private_only"))
        self.hide_channels.setText(tr("dialogs.hide_channels"))
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("dialogs.add"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(
            tr("groups_dialog.cancel")
        )
        self._populate()
