"""Façade **async** au-dessus de Telethon (couche métier, sans Qt).

Frontière entre l'application et le réseau Telegram. Le client Telethon est créé
paresseusement (``client_factory``), ce qui permet de l'injecter dans les tests sans
installer Telethon ni accéder au réseau.

Principe II : on ne contourne aucune restriction d'accès ; on rapporte le statut.
Principe III : toutes les opérations réseau sont ``async`` (consommées via qasync).
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import Any

from pilottelega.app.logging_conf import get_logger
from pilottelega.core.models import AccessStatus, Member, TargetGroup

logger = get_logger(__name__)


class LoginStep(StrEnum):
    """Étape atteinte après soumission du code de connexion."""

    CONNECTED = "connected"
    PASSWORD_REQUIRED = "password_required"


def classify_access_error(exc: Exception) -> AccessStatus:
    """Mappe une exception Telethon vers un ``AccessStatus`` (sans importer Telethon).

    La classification se fait par **nom de classe** afin de rester testable avec des
    exceptions de remplacement.
    """
    name = type(exc).__name__
    if "ChatAdminRequired" in name:
        return AccessStatus.ADMIN_REQUIRED
    return AccessStatus.ERROR


class TelegramService:
    """Gère la connexion et la récupération des membres pour un compte Telegram."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_path: str,
        client_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_path = session_path
        self._client_factory = client_factory or self._default_client_factory
        self._client: Any | None = None
        self._phone: str | None = None

    def _default_client_factory(self) -> Any:
        """Crée un vrai client Telethon (import différé pour la testabilité)."""
        from telethon import TelegramClient

        return TelegramClient(self.session_path, self.api_id, self.api_hash)

    async def _ensure_client(self) -> Any:
        """Crée et connecte le client si nécessaire, puis le retourne."""
        if self._client is None:
            self._client = self._client_factory()
            await self._client.connect()
        return self._client

    # ----- Cycle de connexion (US1 / FR-001..005) -----------------------------------

    async def is_authorized(self) -> bool:
        """Vrai si une session locale valide existe déjà (FR-005)."""
        client = await self._ensure_client()
        return await client.is_user_authorized()

    async def start_login(self, phone: str) -> None:
        """Envoie le code de connexion au numéro fourni (transition CODE_SENT)."""
        self._phone = phone
        client = await self._ensure_client()
        await client.send_code_request(phone)
        logger.info("Code de connexion demandé.")

    async def submit_code(self, code: str) -> LoginStep:
        """Soumet le code reçu.

        Retourne ``CONNECTED`` si la connexion est complète, ou ``PASSWORD_REQUIRED``
        si une vérification 2FA est nécessaire. Toute autre erreur est propagée pour
        affichage d'un message clair (FR-017).
        """
        client = await self._ensure_client()
        try:
            await client.sign_in(self._phone, code)
        except Exception as exc:  # noqa: BLE001 - on distingue le cas 2FA par nom de classe
            if type(exc).__name__ == "SessionPasswordNeededError":
                logger.info("Mot de passe 2FA requis.")
                return LoginStep.PASSWORD_REQUIRED
            logger.warning("Échec de connexion (code): %s", type(exc).__name__)
            raise
        logger.info("Connexion réussie (sans 2FA).")
        return LoginStep.CONNECTED

    async def submit_password(self, password: str) -> None:
        """Valide le mot de passe 2FA (transition → CONNECTED)."""
        client = await self._ensure_client()
        await client.sign_in(password=password)
        logger.info("Connexion réussie (2FA validée).")

    # ----- Récupération des membres (US2 / FR-008..011) -----------------------------

    @staticmethod
    def _to_member(user: Any) -> Member:
        """Convertit un participant Telethon en ``Member`` (identité = ``user.id``)."""
        first = getattr(user, "first_name", "") or ""
        last = getattr(user, "last_name", "") or ""
        display = f"{first} {last}".strip()
        return Member(
            user_id=user.id,
            username=getattr(user, "username", None),
            display_name=display,
        )

    async def fetch_group(self, identifier: str) -> TargetGroup:
        """Récupère les membres d'un groupe et en déduit le ``AccessStatus``.

        N'élève jamais d'exception sur un accès refusé : encode le statut (FR-008/010/011).
        L'échec d'un groupe n'affecte pas les autres (FR-007).
        """
        client = await self._ensure_client()
        group = TargetGroup(raw_input=identifier, identifier=identifier)
        try:
            entity = await client.get_entity(identifier)
            group.title = getattr(entity, "title", None)
            group.handle = getattr(entity, "username", None)
            members = [self._to_member(user) async for user in client.iter_participants(entity)]
            group.members = members
            group.access_status = AccessStatus.FULL if members else AccessStatus.PARTIAL_HIDDEN
        except Exception as exc:  # noqa: BLE001 - statut encodé, pas de propagation (FR-011)
            group.access_status = classify_access_error(exc)
            group.error_message = str(exc) or type(exc).__name__
            logger.warning(
                "fetch_group(%s) -> %s (%s)",
                identifier,
                group.access_status.value,
                type(exc).__name__,
            )
        return group
