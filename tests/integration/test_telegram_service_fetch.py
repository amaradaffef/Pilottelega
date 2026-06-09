"""Tests d'intégration de ``fetch_group`` → ``AccessStatus`` (T017 / US2).

Client Telethon injecté : aucun réseau. Couvre FULL / PARTIAL_HIDDEN / ADMIN_REQUIRED / ERROR.
"""

from __future__ import annotations

from pilottelega.core.models import AccessStatus
from pilottelega.core.telegram_service import TelegramService


class ChatAdminRequiredError(Exception):
    """Réplique le nom de l'exception Telethon (classifiée par nom)."""


class FakeUser:
    def __init__(self, uid, username=None, first="", last=""):
        self.id = uid
        self.username = username
        self.first_name = first
        self.last_name = last


class FakeEntity:
    def __init__(self, title="Groupe", username=None):
        self.title = title
        self.username = username


class FakeClient:
    """Client contrôlable : ``users`` à itérer ou exception à lever."""

    def __init__(self, *, users=None, entity=None, entity_error=None, iter_error=None):
        self._users = users or []
        self._entity = entity or FakeEntity()
        self._entity_error = entity_error
        self._iter_error = iter_error

    async def connect(self):
        pass

    async def get_entity(self, identifier):
        if self._entity_error:
            raise self._entity_error
        return self._entity

    async def _aiter(self):
        if self._iter_error:
            raise self._iter_error
        for u in self._users:
            yield u

    def iter_participants(self, entity):
        return self._aiter()


def _service(client):
    return TelegramService(1, "hash", "ignored", client_factory=lambda: client)


async def test_fetch_full_access():
    users = [FakeUser(1, "alice", "Alice"), FakeUser(2, None, "Bob")]
    group = await _service(FakeClient(users=users, entity=FakeEntity("G", "g"))).fetch_group("@g")
    assert group.access_status is AccessStatus.FULL
    assert {m.user_id for m in group.members} == {1, 2}
    assert group.handle == "g"


async def test_fetch_partial_hidden_when_empty():
    group = await _service(FakeClient(users=[])).fetch_group("@g")
    assert group.access_status is AccessStatus.PARTIAL_HIDDEN
    assert group.members == []


async def test_fetch_admin_required():
    client = FakeClient(iter_error=ChatAdminRequiredError("admin"))
    group = await _service(client).fetch_group("@g")
    assert group.access_status is AccessStatus.ADMIN_REQUIRED


async def test_fetch_error_on_entity_failure():
    client = FakeClient(entity_error=ValueError("introuvable"))
    group = await _service(client).fetch_group("@g")
    assert group.access_status is AccessStatus.ERROR
    assert group.error_message
