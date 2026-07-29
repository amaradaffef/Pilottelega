"""Tests d'intégration de l'accès aux groupes **privés** (ID numérique / lien d'invitation).

Client Telethon injecté : aucun réseau. Vérifie que l'identifiant transmis à Telethon est
correct (int pour un ID, entité issue de l'invitation) et que le refus est explicite.
"""

from __future__ import annotations

from pilottelega.core.models import AccessStatus
from pilottelega.core.telegram_service import DialogInfo, TelegramService


class FakeUser:
    def __init__(self, uid, username=None, first=""):
        self.id = uid
        self.username = username
        self.first_name = first
        self.last_name = ""


class FakeEntity:
    def __init__(self, title="Groupe", username=None, broadcast=False, count=None):
        self.title = title
        self.username = username
        self.broadcast = broadcast
        self.participants_count = count


class FakeDialog:
    def __init__(self, dialog_id, entity, *, is_group=True, is_channel=False, name=None):
        self.id = dialog_id
        self.entity = entity
        self.is_group = is_group
        self.is_channel = is_channel
        self.name = name or getattr(entity, "title", "")


class FakeTotalList(list):
    total = None


class FakeClient:
    """Enregistre l'identifiant reçu par ``get_entity`` et sert des discussions."""

    def __init__(self, *, users=None, entity=None, dialogs=None):
        self._users = users or []
        self._entity = entity or FakeEntity()
        self._dialogs = dialogs or []
        self.entity_calls: list[object] = []

    async def connect(self):
        pass

    async def get_entity(self, identifier):
        self.entity_calls.append(identifier)
        if isinstance(identifier, str) and identifier.lstrip("-").isdigit():
            # Reproduit le comportement de Telethon : un ID en chaîne est pris pour un
            # numéro de téléphone et ne résout aucun groupe.
            raise ValueError(f"Cannot find any entity corresponding to {identifier!r}")
        return self._entity

    async def get_participants(self, entity, limit=0):
        tl = FakeTotalList()
        tl.total = len(self._users)
        return tl

    async def _aiter_participants(self, search):
        for user in self._users:
            yield user

    def iter_participants(self, entity, search=None):
        return self._aiter_participants(search)

    async def _aiter_dialogs(self):
        for dialog in self._dialogs:
            yield dialog

    def iter_dialogs(self):
        return self._aiter_dialogs()


def _service(client, invite_checker=None):
    return TelegramService(
        1, "hash", "ignored", client_factory=lambda: client, invite_checker=invite_checker
    )


async def test_private_group_by_numeric_id_is_resolved_as_int():
    client = FakeClient(users=[FakeUser(1, "alice")], entity=FakeEntity("Privé"))
    group = await _service(client).fetch_group("-1001234567890")
    assert client.entity_calls == [-1001234567890]  # int, pas une chaîne
    assert group.access_status is AccessStatus.FULL
    assert group.title == "Privé"


async def test_public_group_still_resolved_as_username():
    client = FakeClient(users=[FakeUser(1, "alice")], entity=FakeEntity("G", "g"))
    await _service(client).fetch_group("@g")
    assert client.entity_calls == ["@g"]


async def test_invite_link_uses_invite_checker_when_member():
    entity = FakeEntity("Groupe privé")
    seen: list[str] = []

    async def checker(client, invite):
        seen.append(invite)
        return entity

    client = FakeClient(users=[FakeUser(1, "alice")])
    group = await _service(client, invite_checker=checker).fetch_group("+AbCdEf")
    assert seen == ["AbCdEf"]
    assert client.entity_calls == []  # résolu par l'invitation, pas par get_entity
    assert group.access_status is AccessStatus.FULL
    assert group.title == "Groupe privé"


async def test_invite_link_reports_clear_error_when_not_member():
    async def checker(client, invite):
        return None  # aperçu seul : le compte n'est pas membre

    group = await _service(FakeClient(), invite_checker=checker).fetch_group("t.me/+AbCdEf")
    assert group.access_status is AccessStatus.ERROR
    assert "priv" in (group.error_message or "").lower()


async def test_list_dialogs_returns_public_and_private_groups():
    dialogs = [
        FakeDialog(-1001, FakeEntity("Public", username="pub", count=42)),
        FakeDialog(-1002, FakeEntity("Privé", count=7)),
        FakeDialog(-1003, FakeEntity("Canal", broadcast=True), is_group=False, is_channel=True),
        FakeDialog(999, FakeUser(999, "bob"), is_group=False),  # conversation individuelle
    ]
    result = await _service(FakeClient(dialogs=dialogs)).list_dialogs()
    assert [d.identifier for d in result] == ["@pub", "-1002", "-1003"]
    assert [d.is_private for d in result] == [False, True, True]
    assert [d.is_channel for d in result] == [False, False, True]
    assert result[1].members_count == 7


def test_dialog_info_label():
    info = DialogInfo(identifier="-1002", title="Privé", is_private=True)
    assert info.label == "Privé — -1002"
