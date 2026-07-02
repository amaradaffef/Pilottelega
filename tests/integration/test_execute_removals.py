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


async def test_execute_removals_uses_input_peer_with_access_hash():
    """Avec un access_hash, on passe un InputPeerUser résolu (évite l'échec de résolution)."""
    from telethon.tl.types import InputPeerUser

    captured: list[object] = []

    class CapturingClient(FakeClient):
        async def kick_participant(self, entity, user):
            captured.append(user)

    client = CapturingClient()
    results = await _service(client).execute_removals([Removal("@g", "g", 100, "x", 555)])
    assert results[0].ok
    assert isinstance(captured[0], InputPeerUser)
    assert captured[0].user_id == 100
    assert captured[0].access_hash == 555


async def test_execute_removals_prefers_username_resolution():
    """Si un username existe, on le résout via get_input_entity (access_hash « complet »)."""
    captured: list[object] = []

    class ResolvingClient(FakeClient):
        async def get_input_entity(self, handle):
            captured.append(("resolve", handle))
            return ("resolved", handle)

        async def kick_participant(self, entity, user):
            captured.append(("kick", user))

    client = ResolvingClient()
    results = await _service(client).execute_removals([Removal("@g", "g", 100, "@neo", 555, "neo")])
    assert results[0].ok
    # Le username prime sur l'access_hash : on résout '@neo' puis on kicke la référence obtenue.
    assert ("resolve", "@neo") in captured
    assert ("kick", ("resolved", "@neo")) in captured


async def test_execute_removals_failure_reports_detail():
    """Le message d'erreur réel est conservé dans le résultat (diagnostic utilisateur)."""
    client = FakeClient(fail_for={("@g", 1)})
    results = await _service(client).execute_removals([Removal("@g", "g", 1, "a")])
    assert results[0].ok is False
    assert results[0].error == "droits insuffisants"


class FloodWaitError(Exception):
    """Imitation de telethon.errors.FloodWaitError (détecté par nom de classe + .seconds)."""

    def __init__(self, seconds: int) -> None:
        super().__init__(f"A wait of {seconds} seconds is required")
        self.seconds = seconds


async def test_execute_removals_waits_and_retries_on_flood():
    """Un FloodWait provoque une pause puis une nouvelle tentative (au lieu d'un échec)."""
    waits: list[int] = []

    class FloodyClient(FakeClient):
        def __init__(self) -> None:
            super().__init__()
            self._first = True

        async def kick_participant(self, entity, user):
            if self._first:
                self._first = False
                raise FloodWaitError(0)  # seconds=0 -> pause immédiate en test
            self.kicked.append((entity[1], user))

    client = FloodyClient()
    results = await _service(client).execute_removals(
        [Removal("@g", "g", 1, "a")], on_wait=lambda s, d, t: waits.append(s)
    )
    assert results[0].ok is True
    assert waits == [0]  # on a bien patienté une fois
    assert client.kicked == [("@g", 1)]
