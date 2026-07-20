"""Point d'entrée de Pilottelega : bootstrap **qasync** + routage onboarding/principal.

Le pont qasync est câblé ici (Principe III) : asyncio tourne dans la boucle d'événements Qt,
de sorte que les appels réseau Telethon ne gèlent jamais l'interface.
"""

from __future__ import annotations

import asyncio
import sys

from pilottelega.app import i18n, paths, preferences, settings
from pilottelega.app.logging_conf import get_logger

logger = get_logger(__name__)


def main() -> int:
    """Lance l'application. Retourne le code de sortie du processus.

    Le routage de démarrage (FR-005) : si une session locale valide existe, on ouvre
    directement la fenêtre principale, sinon l'écran d'onboarding.
    """
    # Imports Qt différés pour garder le module importable sans environnement graphique
    # (tests, CI). L'UI n'est jamais importée par la couche métier.
    from PySide6.QtWidgets import QApplication
    from qasync import QEventLoop

    from pilottelega.core.telegram_service import TelegramService
    from pilottelega.ui import theme
    from pilottelega.ui.main_window import MainWindow
    from pilottelega.ui.onboarding import OnboardingDialog

    # Applique la langue mémorisée (FR/EN/RU) avant de construire l'interface.
    i18n.set_language(preferences.load_language())

    app = QApplication(sys.argv)
    # Thème global (clair/sombre) selon la préférence enregistrée.
    theme.apply_theme(app, preferences.load_dark_mode())
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # L'événement de fermeture permet de quitter proprement la boucle qasync quand
    # la dernière fenêtre est fermée (sinon run_forever ne rendrait jamais la main).
    app_close = asyncio.Event()
    app.aboutToQuit.connect(app_close.set)

    config = settings.load_config()
    service: TelegramService | None = None
    if config and config.is_complete():
        service = TelegramService(
            api_id=config.api_id,
            api_hash=config.api_hash,
            session_path=str(paths.session_path()),
        )

    # Référence conservée pour empêcher le garbage collector de fermer la fenêtre
    # dès la fin de la coroutine de routage (cause classique de « rien ne s'affiche »).
    windows: list[object] = []

    async def _run() -> None:
        """Choisit l'écran de départ (FR-005) puis attend la fermeture de l'application."""
        authorized = False
        if service is not None:
            try:
                authorized = await service.is_authorized()
            except Exception as exc:  # noqa: BLE001 - on dégrade proprement vers l'onboarding
                logger.warning("Vérification de session échouée: %s", type(exc).__name__)
                authorized = False

        if authorized and service is not None:
            window: object = MainWindow(service)
        else:
            window = OnboardingDialog()
        windows.append(window)
        window.show()  # type: ignore[attr-defined]

        await app_close.wait()

    with loop:
        loop.run_until_complete(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
