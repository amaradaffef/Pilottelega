"""Écran d'onboarding (premier lancement) — saisie des identifiants et connexion.

Affiché quand aucune session locale valide n'existe (FR-001/005). Tous les appels réseau
sont ``await``-és via qasync : l'interface ne gèle pas (Principe III). Aucun secret n'est
journalisé (Principe II). Interface traduisible (FR/EN/RU).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from pilottelega.app import i18n, paths, preferences, settings
from pilottelega.app.i18n import tr
from pilottelega.app.logging_conf import get_logger
from pilottelega.core.telegram_service import LoginStep, TelegramService

logger = get_logger(__name__)

API_TOOLS_URL = "https://my.telegram.org"


class OnboardingDialog(QWidget):
    """Fenêtre de configuration initiale et de connexion."""

    def __init__(self) -> None:
        super().__init__()
        self._service: TelegramService | None = None

        layout = QVBoxLayout(self)

        # Sélecteur de langue
        lang_row = QHBoxLayout()
        lang_row.addStretch()
        self.lang_label = QLabel()
        lang_row.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        for code, name in i18n.AVAILABLE_LANGUAGES.items():
            self.lang_combo.addItem(name, code)
        self.lang_combo.setCurrentIndex(self.lang_combo.findData(i18n.get_language()))
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_row.addWidget(self.lang_combo)
        layout.addLayout(lang_row)

        self.intro = QLabel()
        self.intro.setTextFormat(Qt.TextFormat.RichText)
        self.intro.setOpenExternalLinks(True)
        self.intro.setWordWrap(True)
        layout.addWidget(self.intro)

        # Étape 1 : identifiants
        form = QFormLayout()
        self.api_id_edit = QLineEdit()
        self.api_hash_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+33...")
        self.phone_label = QLabel()
        form.addRow("api_id", self.api_id_edit)
        form.addRow("api_hash", self.api_hash_edit)
        form.addRow(self.phone_label, self.phone_edit)
        layout.addLayout(form)

        self.send_code_btn = QPushButton()
        self.send_code_btn.clicked.connect(self.on_send_code)
        layout.addWidget(self.send_code_btn)

        # Étape 2 : code + 2FA (masquées au départ)
        self.code_edit = QLineEdit()
        self.code_edit.setVisible(False)
        layout.addWidget(self.code_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setVisible(False)
        layout.addWidget(self.password_edit)

        self.confirm_btn = QPushButton()
        self.confirm_btn.clicked.connect(self.on_confirm)
        self.confirm_btn.setVisible(False)
        layout.addWidget(self.confirm_btn)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.retranslate()

    def retranslate(self) -> None:
        """Met à jour tous les textes selon la langue courante."""
        self.setWindowTitle(tr("onboarding.title"))
        self.lang_label.setText(tr("common.language"))
        self.intro.setText(tr("onboarding.intro", url=API_TOOLS_URL))
        self.phone_label.setText(tr("onboarding.phone"))
        self.send_code_btn.setText(tr("onboarding.send_code"))
        self.code_edit.setPlaceholderText(tr("onboarding.code_placeholder"))
        self.password_edit.setPlaceholderText(tr("onboarding.password_placeholder"))
        self.confirm_btn.setText(tr("onboarding.connect"))

    def on_language_changed(self) -> None:
        """Applique et mémorise la langue sélectionnée."""
        code = self.lang_combo.currentData()
        i18n.set_language(code)
        preferences.save_language(code)
        self.retranslate()

    def _set_busy(self, busy: bool, message: str = "") -> None:
        """Désactive les boutons pendant une opération réseau et affiche un statut."""
        self.send_code_btn.setEnabled(not busy)
        self.confirm_btn.setEnabled(not busy)
        if message:
            self.status.setText(message)

    @asyncSlot()
    async def on_send_code(self) -> None:
        """Valide les identifiants et déclenche l'envoi du code (FR-002)."""
        try:
            api_id = int(self.api_id_edit.text().strip())
        except ValueError:
            self.status.setText(tr("onboarding.api_id_error"))
            return
        api_hash = self.api_hash_edit.text().strip()
        phone = self.phone_edit.text().strip()
        if not api_hash or not phone:
            self.status.setText(tr("onboarding.fill_fields"))
            return

        self._service = TelegramService(
            api_id=api_id, api_hash=api_hash, session_path=str(paths.session_path())
        )
        self._set_busy(True, tr("onboarding.sending_code"))
        try:
            await self._service.start_login(phone)
        except Exception as exc:  # noqa: BLE001 - message clair, pas de plantage (FR-017)
            logger.warning("Échec d'envoi du code: %s", type(exc).__name__)
            self._set_busy(False, tr("onboarding.send_failed"))
            return

        settings.save_config(settings.AppConfig(api_id=api_id, api_hash=api_hash, phone=phone))
        self.code_edit.setVisible(True)
        self.password_edit.setVisible(True)
        self.confirm_btn.setVisible(True)
        self._set_busy(False, tr("onboarding.code_sent"))

    @asyncSlot()
    async def on_confirm(self) -> None:
        """Soumet le code puis, si nécessaire, le mot de passe 2FA."""
        if self._service is None:
            return
        code = self.code_edit.text().strip()
        if not code:
            self.status.setText(tr("onboarding.enter_code"))
            return

        self._set_busy(True, tr("onboarding.connecting"))
        try:
            step = await self._service.submit_code(code)
            if step is LoginStep.PASSWORD_REQUIRED:
                password = self.password_edit.text()
                if not password:
                    self._set_busy(False, tr("onboarding.need_password"))
                    return
                await self._service.submit_password(password)
        except Exception as exc:  # noqa: BLE001 - message clair (FR-017)
            logger.warning("Échec de connexion: %s", type(exc).__name__)
            self._set_busy(False, tr("onboarding.login_failed"))
            return

        self._open_main_window()

    def _open_main_window(self) -> None:
        """Ouvre la fenêtre principale après connexion réussie."""
        from pilottelega.ui.main_window import MainWindow

        assert self._service is not None
        self._main_window = MainWindow(self._service)
        self._main_window.show()
        self.close()
        QMessageBox.information(self._main_window, tr("app.title"), tr("onboarding.welcome"))
