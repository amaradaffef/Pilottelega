"""Écran d'onboarding (premier lancement) — saisie des identifiants et connexion.

Affiché quand aucune session locale valide n'existe (FR-001/005). Tous les appels réseau
sont ``await``-és via qasync : l'interface ne gèle pas (Principe III). Aucun secret n'est
journalisé (Principe II).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qasync import asyncSlot

from pilottelega.app import paths, settings
from pilottelega.app.logging_conf import get_logger
from pilottelega.core.telegram_service import LoginStep, TelegramService

logger = get_logger(__name__)

API_TOOLS_URL = "https://my.telegram.org"


class OnboardingDialog(QWidget):
    """Fenêtre de configuration initiale et de connexion."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Pilottelega — Connexion")
        self._service: TelegramService | None = None

        layout = QVBoxLayout(self)

        intro = QLabel(
            "Pour utiliser Pilottelega, vous avez besoin d'un identifiant d'accès Telegram "
            "personnel et <b>gratuit</b>.<br>"
            f"Créez-le ici : <a href='{API_TOOLS_URL}'>{API_TOOLS_URL}</a> "
            "(section « API development tools »).<br>"
            "Vos identifiants restent <b>uniquement sur votre PC</b>."
        )
        intro.setTextFormat(Qt.TextFormat.RichText)
        intro.setOpenExternalLinks(True)
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # Étape 1 : identifiants
        form = QFormLayout()
        self.api_id_edit = QLineEdit()
        self.api_hash_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+33...")
        form.addRow("api_id", self.api_id_edit)
        form.addRow("api_hash", self.api_hash_edit)
        form.addRow("Téléphone", self.phone_edit)
        layout.addLayout(form)

        self.send_code_btn = QPushButton("Envoyer le code")
        self.send_code_btn.clicked.connect(self.on_send_code)
        layout.addWidget(self.send_code_btn)

        # Étape 2 : code + 2FA (masquées au départ)
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Code reçu dans Telegram")
        self.code_edit.setVisible(False)
        layout.addWidget(self.code_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Mot de passe 2FA (si activé)")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setVisible(False)
        layout.addWidget(self.password_edit)

        self.confirm_btn = QPushButton("Se connecter")
        self.confirm_btn.clicked.connect(self.on_confirm)
        self.confirm_btn.setVisible(False)
        layout.addWidget(self.confirm_btn)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

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
            self.status.setText("L'api_id doit être un nombre.")
            return
        api_hash = self.api_hash_edit.text().strip()
        phone = self.phone_edit.text().strip()
        if not api_hash or not phone:
            self.status.setText("Renseignez api_hash et le numéro de téléphone.")
            return

        self._service = TelegramService(
            api_id=api_id, api_hash=api_hash, session_path=str(paths.session_path())
        )
        self._set_busy(True, "Envoi du code en cours…")
        try:
            await self._service.start_login(phone)
        except Exception as exc:  # noqa: BLE001 - message clair, pas de plantage (FR-017)
            logger.warning("Échec d'envoi du code: %s", type(exc).__name__)
            self._set_busy(False, "Échec de l'envoi du code. Vérifiez vos identifiants.")
            return

        # Mémorise la config (les identifiants sont valides côté format)
        settings.save_config(settings.AppConfig(api_id=api_id, api_hash=api_hash, phone=phone))
        self.code_edit.setVisible(True)
        self.password_edit.setVisible(True)
        self.confirm_btn.setVisible(True)
        self._set_busy(
            False, "Code envoyé : saisissez-le ci-dessous (et le mot de passe 2FA si activé)."
        )

    @asyncSlot()
    async def on_confirm(self) -> None:
        """Soumet le code puis, si nécessaire, le mot de passe 2FA."""
        if self._service is None:
            return
        code = self.code_edit.text().strip()
        if not code:
            self.status.setText("Saisissez le code reçu.")
            return

        self._set_busy(True, "Connexion en cours…")
        try:
            step = await self._service.submit_code(code)
            if step is LoginStep.PASSWORD_REQUIRED:
                password = self.password_edit.text()
                if not password:
                    self._set_busy(False, "Ce compte a la 2FA : saisissez votre mot de passe.")
                    return
                await self._service.submit_password(password)
        except Exception as exc:  # noqa: BLE001 - message clair (FR-017)
            logger.warning("Échec de connexion: %s", type(exc).__name__)
            self._set_busy(False, "Connexion échouée. Vérifiez le code / mot de passe.")
            return

        self._open_main_window()

    def _open_main_window(self) -> None:
        """Ouvre la fenêtre principale après connexion réussie."""
        from pilottelega.ui.main_window import MainWindow

        assert self._service is not None
        self._main_window = MainWindow(self._service)
        self._main_window.show()
        self.close()
        QMessageBox.information(self._main_window, "Pilottelega", "Connexion réussie. Bienvenue !")
