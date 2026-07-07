"""Tests de la vérification de comptes par @username (client Telethon injecté)."""

from __future__ import annotations

from pilottelega.core.telegram_service import TelegramService, classify_entity


class FakeUser:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeChannel:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


# classify_entity détecte le type par nom de classe : on renomme les classes de test.
FakeUser.__name__ = "User"
FakeChannel.__name__ = "Channel"


class UsernameNotOccupiedError(Exception):
    pass


class FloodWaitError(Exception):
    def __init__(self, seconds):
        super().__init__(f"A wait of {seconds} seconds is required")
        self.seconds = seconds


class FakeClient:
    def __init__(self, mapping=None, errors=None):
        self._mapping = mapping or {}
        self._errors = errors or {}

    async def connect(self):
        pass

    async def get_entity(self, handle):
        if handle in self._errors:
            raise self._errors[handle]
        if handle in self._mapping:
            return self._mapping[handle]
        raise UsernameNotOccupiedError("No user has that username")


def _service(client):
    return TelegramService(1, "hash", "ignored", client_factory=lambda: client)


def test_classify_entity_user_and_bot():
    assert classify_entity(FakeUser(id=1, first_name="Ann", bot=False))[0] == "user"
    assert classify_entity(FakeUser(id=2, first_name="Botty", bot=True))[0] == "bot"
    kind, deleted, name, eid = classify_entity(FakeUser(id=3, deleted=True))
    assert deleted is True and kind == "user" and eid == 3


def test_classify_entity_channel_vs_group():
    assert classify_entity(FakeChannel(id=1, title="News", broadcast=True))[0] == "channel"
    assert classify_entity(FakeChannel(id=2, title="Chat", megagroup=True))[0] == "group"


async def test_check_usernames_found_and_missing():
    client = FakeClient(mapping={"@ann": FakeUser(id=1, first_name="Ann", bot=False)})
    results = await _service(client).check_usernames(["ann", "@ghost"])
    assert results[0].found is True and results[0].kind == "user" and results[0].name == "Ann"
    assert results[1].found is False and results[1].username == "@ghost"


async def test_check_usernames_retries_on_flood():
    waits: list[int] = []

    class FloodyClient(FakeClient):
        def __init__(self):
            super().__init__()
            self._first = True

        async def get_entity(self, handle):
            if self._first:
                self._first = False
                raise FloodWaitError(0)
            return FakeUser(id=9, first_name="Z", bot=False)

    results = await _service(FloodyClient()).check_usernames(
        ["z"], on_wait=lambda s, d, t: waits.append(s)
    )
    assert results[0].found is True
    assert waits == [0]
