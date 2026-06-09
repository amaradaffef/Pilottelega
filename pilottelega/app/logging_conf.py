"""Configuration de la journalisation (module ``logging``, jamais ``print``).

Aucun secret (``api_hash``, mot de passe, code) ne doit être journalisé.
"""

from __future__ import annotations

import logging

_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    """Configure le logger racine une seule fois."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger nommé après avoir garanti la configuration."""
    configure_logging()
    return logging.getLogger(name)
