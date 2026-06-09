"""Point d'entrée de Pilottelega : bootstrap **qasync** + routage onboarding/principal.

Le pont qasync est câblé ici (Principe III) : asyncio tourne dans la boucle d'événements Qt,
de sorte que les appels réseau Telethon ne gèlent jamais l'interface.
"""

from __future__ import annotations

import asyncio
import sys

from pilottelega.app import paths, settings
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
    from pilottelega.ui.main_window import MainWindow
    from pilottelega.ui.onboarding import OnboardingDialog

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    config = settings.load_config()
    service: TelegramService | None = None
    if config and config.is_complete():
        service = TelegramService(
            api_id=config.api_id,
            api_hash=config.api_hash,
            session_path=str(paths.session_path()),
        )

    async def _route() -> None:
        """Décide de l'écran de départ selon l'existence d'une session valide."""
        nonlocal service
        authorized = False
        if service is not None:
            try:
                authorized = await service.is_authorized()
            except Exception as exc:  # noqa: BLE001 - on dégrade proprement vers l'onboarding
                logger.warning("Vérification de session échouée: %s", type(exc).__name__)
                authorized = False

        if authorized and service is not None:
            window = MainWindow(service)
            window.show()
        else:
            dialog = OnboardingDialog()
            dialog.show()

    with loop:
        loop.create_task(_route())
        loop.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
