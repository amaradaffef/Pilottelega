"""Tests d'intégration de l'exécution des retraits (client Telethon injecté)."""

from __future__ import annotations

from pilottelega.core.removal import Removal
from pilottelega.core.telegram_service import TelegramService


class FakeClient:
    """Enregistre les kicks/bans ; peut échouer pour certains (groupe, user)."""

    def __init__(self, fail_for=None):
        self.kicked: list[tuple[str, int]] = []
        self.banned: list[tuple[str, int]] = []
        self._fail = fail_for or set()

    async def connect(self):
        pass

    async def get_entity(self, identifier):
        return ("entity", identifier)

    async def kick_participant(self, entity, user_id):
        if (entity[1], user_id) in self._fail:
            raise RuntimeError("droits insuffisants")
        self.kicked.append((entity[1], user_id))

    async def edit_permissions(self, entity, user_id, view_messages=True):
        self.banned.append((entity[1], user_id))


def _service(client):
    return TelegramService(1, "hash", "ignored", client_factory=lambda: client)


async def test_execute_removals_kick():
    client = FakeClient()
    removals = [Removal("@bravo", "bravo", 1, "a"), Removal("@charlie", "charlie", 1, "a")]
    results = await _service(client).execute_removals(removals)
    assert all(r.ok for r in results)
    assert set(client.kicked) == {("@bravo", 1), ("@charlie", 1)}
    assert client.banned == []


async def test_execute_removals_ban():
    client = FakeClient()
    results = await _service(client).execute_removals([Removal("@g", "g", 5, "x")], ban=True)
    assert results[0].ok
    assert client.banned == [("@g", 5)]
    assert client.kicked == []


async def test_execute_removals_partial_failure_is_isolated():
    client = FakeClient(fail_for={("@bravo", 1)})
    removals = [Removal("@bravo", "bravo", 1, "a"), Removal("@charlie", "charlie", 2, "b")]
    results = await _service(client).execute_removals(removals)
    ok_by_key = {(r.removal.group_identifier, r.removal.user_id): r.ok for r in results}
    assert ok_by_key[("@bravo", 1)] is False
    assert ok_by_key[("@charlie", 2)] is True
    assert client.kicked == [("@charlie", 2)]


async def test_execute_removals_progress_callback():
    client = FakeClient()
    seen = []
    removals = [Removal("@g", "g", i, str(i)) for i in range(3)]
    await _service(client).execute_removals(removals, progress=lambda d, t: seen.append((d, t)))
    assert seen == [(1, 3), (2, 3), (3, 3)]
