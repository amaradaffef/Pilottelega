"""Façade **async** au-dessus de Telethon (couche métier, sans Qt).

Frontière entre l'application et le réseau Telegram. Le client Telethon est créé
paresseusement (``client_factory``), ce qui permet de l'injecter dans les tests sans
installer Telethon ni accéder au réseau.

Principe II : on ne contourne aucune restriction d'accès ; on rapporte le statut.
Principe III : toutes les opérations réseau sont ``async`` (consommées via qasync).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import replace
from enum import StrEnum
from typing import Any

from pilottelega.app.logging_conf import get_logger
from pilottelega.core.models import AccessStatus, Member, TargetGroup
from pilottelega.core.removal import Removal, RemovalResult

logger = get_logger(__name__)


class LoginStep(StrEnum):
    """Étape atteinte après soumission du code de connexion."""

    CONNECTED = "connected"
    PASSWORD_REQUIRED = "password_required"


def format_last_seen(user: Any) -> str | None:
    """Représente la dernière connexion d'un utilisateur en chaîne exportable.

    Si le statut porte une date (``UserStatusOffline.was_online``), on l'exporte en ISO ;
    sinon on retourne une valeur lisible (online, recently, last_week…). Détection par nom
    de classe pour éviter d'importer les types Telethon.
    """
    status = getattr(user, "status", None)
    if status is None:
        return None
    was_online = getattr(status, "was_online", None)
    if was_online is not None:
        try:
            return was_online.isoformat()
        except AttributeError:
            return str(was_online)
    mapping = {
        "UserStatusOnline": "online",
        "UserStatusRecently": "recently",
        "UserStatusLastWeek": "last_week",
        "UserStatusLastMonth": "last_month",
        "UserStatusOffline": "offline",
        "UserStatusEmpty": "",
    }
    return mapping.get(type(status).__name__, type(status).__name__)


# Requêtes de recherche pour la récupération « complète » : en combinant une recherche
# vide + chaque lettre (latin/cyrillique) + chiffres, on remonte bien plus de membres que
# la pagination par défaut (que Telegram plafonne sur les gros groupes).
_SEARCH_QUERIES: list[str] = [
    "",
    *"abcdefghijklmnopqrstuvwxyz",
    *"абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    *"0123456789",
]


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
        about_fetcher: Callable[[Any, int], Any] | None = None,
    ) -> None:
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_path = session_path
        self._client_factory = client_factory or self._default_client_factory
        # Récupérateur de bio injectable (testable sans Telethon).
        self._about_fetcher = about_fetcher or self._default_about_fetcher
        self._client: Any | None = None
        self._phone: str | None = None
        self._me: Any | None = None

    def _default_client_factory(self) -> Any:
        """Crée un vrai client Telethon (import différé pour la testabilité)."""
        from telethon import TelegramClient

        return TelegramClient(self.session_path, self.api_id, self.api_hash)

    async def _default_about_fetcher(self, client: Any, user_id: int) -> str | None:
        """Récupère la bio (« about ») d'un utilisateur via une requête « full user ».

        Coûteux (une requête réseau par membre) : utilisé seulement si l'option est activée.
        """
        from telethon.tl.functions.users import GetFullUserRequest

        full = await client(GetFullUserRequest(user_id))
        return getattr(full.full_user, "about", None)

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

    async def get_me(self) -> Any:
        """Retourne le compte connecté (mis en cache), ou ``None`` en cas d'échec.

        Sert notamment à ne jamais tenter de se retirer soi-même d'un groupe.
        """
        if self._me is None:
            client = await self._ensure_client()
            try:
                self._me = await client.get_me()
            except Exception as exc:  # noqa: BLE001 - best-effort, ne bloque pas l'appli
                logger.warning("get_me indisponible: %s", type(exc).__name__)
                return None
        return self._me

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
        first = getattr(user, "first_name", None)
        last = getattr(user, "last_name", None)
        display = f"{first or ''} {last or ''}".strip()
        return Member(
            user_id=user.id,
            username=getattr(user, "username", None),
            display_name=display,
            first_name=first,
            last_name=last,
            is_bot=bool(getattr(user, "bot", False)),
            is_premium=bool(getattr(user, "premium", False)),
            is_deleted=bool(getattr(user, "deleted", False)),
            last_seen=format_last_seen(user),
            phone=getattr(user, "phone", None),
            access_hash=getattr(user, "access_hash", None),
        )

    async def _iter_participants(self, client: Any, entity: Any, thorough: bool):
        """Itère les participants ; en mode ``thorough``, combine des recherches par lettre.

        Le mode complet contourne en partie le plafond d'énumération de Telegram sur les
        gros groupes (la déduplication est faite par l'appelant).
        """
        if not thorough:
            async for user in client.iter_participants(entity):
                yield user
            return
        for query in _SEARCH_QUERIES:
            try:
                async for user in client.iter_participants(entity, search=query):
                    yield user
            except Exception as exc:  # noqa: BLE001 - une recherche peut échouer (FloodWait…)
                logger.warning("Recherche '%s' échouée: %s", query, type(exc).__name__)

    @staticmethod
    async def _participants_total(client: Any, entity: Any) -> int | None:
        """Nombre total de membres annoncé par Telegram (``None`` si indisponible).

        Utilise ``get_participants(limit=0)`` qui renvoie le total sans charger la liste.
        Permet de détecter une liste incomplète (gros groupes / canaux de diffusion).
        """
        try:
            probe = await client.get_participants(entity, limit=0)
        except Exception:  # noqa: BLE001 - total best-effort, ne bloque pas le fetch
            return None
        return getattr(probe, "total", None)

    async def _with_description(self, client: Any, member: Member) -> Member:
        """Retourne une copie du membre enrichie de sa bio (best-effort, jamais bloquant)."""
        try:
            about = await self._about_fetcher(client, member.user_id)
        except Exception as exc:  # noqa: BLE001 - une bio manquante ne casse pas le fetch
            logger.warning("Bio indisponible pour %s: %s", member.user_id, type(exc).__name__)
            return member
        return replace(member, description=about)

    async def fetch_group(
        self, identifier: str, fetch_descriptions: bool = False, thorough: bool = False
    ) -> TargetGroup:
        """Récupère les membres d'un groupe et en déduit le ``AccessStatus``.

        ``thorough`` active une récupération complète (recherche par lettres) pour remonter
        davantage de membres sur les gros groupes. ``fetch_descriptions`` complète la bio de
        chaque membre (lent). N'élève jamais d'exception sur un accès refusé : encode le statut
        (FR-008/010/011). L'échec d'un groupe n'affecte pas les autres (FR-007).
        """
        client = await self._ensure_client()
        group = TargetGroup(raw_input=identifier, identifier=identifier)
        try:
            entity = await client.get_entity(identifier)
            group.title = getattr(entity, "title", None)
            group.handle = getattr(entity, "username", None)

            # Nombre total annoncé par Telegram (pour détecter une liste incomplète).
            total = await self._participants_total(client, entity)

            members: list[Member] = []
            seen_ids: set[int] = set()
            async for user in self._iter_participants(client, entity, thorough):
                if user.id in seen_ids:
                    continue
                seen_ids.add(user.id)
                members.append(self._to_member(user))
            if fetch_descriptions:
                members = [await self._with_description(client, m) for m in members]
            group.members = members
            group.total_count = total if total is not None else len(members)

            if not members:
                group.access_status = AccessStatus.PARTIAL_HIDDEN
            elif total is not None and len(members) < total:
                # On a lu moins que le total réel → liste partielle (Telegram restreint).
                group.access_status = AccessStatus.PARTIAL_HIDDEN
            else:
                group.access_status = AccessStatus.FULL
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

    # ----- Retrait de membres (administration) --------------------------------------

    async def _resolve_user(
        self, user_id: int, access_hash: int | None, username: str | None
    ) -> Any:
        """Résout l'utilisateur en une référence acceptée par le bannissement/kick.

        Ordre de préférence :

        1. ``username`` → ``get_input_entity('@name')`` : requête « resolve » qui renvoie un
           access_hash **complet** (fiable pour toutes les opérations).
        2. ``access_hash`` mémorisé → ``InputPeerUser`` (fonctionne si le hash n'est pas « min »).
        3. ``user_id`` seul → résolu via le cache de session Telethon.

        Le hash des participants d'un canal est souvent « min » et provoque
        ``PARTICIPANT_ID_INVALID`` sur ``EditBannedRequest`` : d'où la priorité au username.
        """
        client = self._client
        if username:
            handle = username if username.startswith("@") else f"@{username}"
            return await client.get_input_entity(handle)
        if access_hash is not None:
            from telethon.tl.types import InputPeerUser

            return InputPeerUser(user_id, access_hash)
        return user_id

    async def _remove_one(
        self,
        entity: Any,
        user_id: int,
        ban: bool,
        access_hash: int | None = None,
        username: str | None = None,
    ) -> None:
        """Retire (kick) ou bannit un utilisateur d'un groupe. Lève en cas d'échec."""
        client = self._client
        user = await self._resolve_user(user_id, access_hash, username)
        if ban:
            # view_messages=False => banni (ne peut plus voir/rejoindre).
            await client.edit_permissions(entity, user, view_messages=False)
        else:
            # kick = retire mais autorise un retour ultérieur via lien.
            await client.kick_participant(entity, user)

    @staticmethod
    def _flood_wait_seconds(exc: Exception) -> int | None:
        """Secondes d'attente exigées si l'exception est un ``FloodWaitError``, sinon ``None``."""
        if type(exc).__name__ == "FloodWaitError":
            seconds = getattr(exc, "seconds", None)
            if seconds is not None:
                return int(seconds)
        return None

    async def execute_removals(
        self,
        removals: list[Removal],
        ban: bool = False,
        progress: Callable[[int, int], None] | None = None,
        delay: float = 0.0,
        on_wait: Callable[[int, int, int], None] | None = None,
        max_flood_retries: int = 5,
    ) -> list[RemovalResult]:
        """Exécute une liste de retraits, en rapportant le résultat de **chacun**.

        Un échec sur un retrait (droits manquants, etc.) n'interrompt pas les autres : il est
        consigné dans le ``RemovalResult`` correspondant.

        Anti-flood : Telegram bride les bannissements en masse. On patiente ``delay`` secondes
        entre deux retraits, et si Telegram exige une pause (``FloodWaitError``), on **attend
        puis réessaie** le même retrait (jusqu'à ``max_flood_retries`` fois). ``on_wait`` reçoit
        ``(secondes, déjà_traités, total)`` à chaque pause pour informer l'utilisateur.
        """
        client = await self._ensure_client()
        entity_cache: dict[str, Any] = {}
        results: list[RemovalResult] = []
        total = len(removals)
        for index, removal in enumerate(removals, start=1):
            floods = 0
            while True:
                try:
                    entity = entity_cache.get(removal.group_identifier)
                    if entity is None:
                        entity = await client.get_entity(removal.group_identifier)
                        entity_cache[removal.group_identifier] = entity
                    await self._remove_one(
                        entity, removal.user_id, ban, removal.access_hash, removal.username
                    )
                    results.append(RemovalResult(removal, ok=True))
                    break
                except Exception as exc:  # noqa: BLE001 - un échec ne bloque pas les autres
                    wait = self._flood_wait_seconds(exc)
                    if wait is not None and floods < max_flood_retries:
                        floods += 1
                        logger.info("FloodWait: pause de %ss avant nouvelle tentative.", wait)
                        if on_wait is not None:
                            on_wait(wait, index - 1, total)
                        await asyncio.sleep(wait)
                        continue
                    detail = str(exc) or type(exc).__name__
                    logger.warning(
                        "Retrait échoué (user=%s, group=%s): %s",
                        removal.user_id,
                        removal.group_identifier,
                        detail,
                    )
                    results.append(RemovalResult(removal, ok=False, error=detail))
                    break
            if progress is not None:
                progress(index, total)
            if delay and index < total:
                await asyncio.sleep(delay)
        return results
