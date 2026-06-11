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


class FakeTotalList(list):
    """Imite le ``TotalList`` de Telethon (liste avec attribut ``total``)."""

    total = None


class FakeClient:
    """Client contrôlable : ``users`` à itérer ou exception à lever."""

    def __init__(
        self, *, users=None, entity=None, entity_error=None, iter_error=None, total=None, cap=None
    ):
        self._users = users or []
        self._entity = entity or FakeEntity()
        self._entity_error = entity_error
        self._iter_error = iter_error
        self._total = total
        self._cap = cap  # simule le plafond de la pagination par défaut

    async def connect(self):
        pass

    async def get_entity(self, identifier):
        if self._entity_error:
            raise self._entity_error
        return self._entity

    async def get_participants(self, entity, limit=0):
        tl = FakeTotalList()
        tl.total = self._total
        return tl

    async def _aiter(self, search):
        if self._iter_error:
            raise self._iter_error
        # En mode recherche (thorough), on renvoie les membres dont le nom commence par la
        # lettre demandée ; sinon (search None/"") on renvoie tout (pagination par défaut).
        if search:
            for u in self._users:
                name = (u.first_name or "").lower()
                if name.startswith(search):
                    yield u
        else:
            pool = self._users if self._cap is None else self._users[: self._cap]
            for u in pool:
                yield u

    def iter_participants(self, entity, search=None):
        return self._aiter(search)


def _service(client):
    return TelegramService(1, "hash", "ignored", client_factory=lambda: client)


async def test_fetch_full_access():
    users = [FakeUser(1, "alice", "Alice"), FakeUser(2, None, "Bob")]
    group = await _service(FakeClient(users=users, entity=FakeEntity("G", "g"))).fetch_group("@g")
    assert group.access_status is AccessStatus.FULL
    assert {m.user_id for m in group.members} == {1, 2}
    assert group.handle == "g"


async def test_fetch_partial_when_total_exceeds_fetched():
    # Telegram annonce 10 membres mais n'en laisse lire que 2 (cas admin/canal/gros groupe).
    users = [FakeUser(1, "alice"), FakeUser(2, "bob")]
    group = await _service(FakeClient(users=users, total=10)).fetch_group("@g")
    assert group.access_status is AccessStatus.PARTIAL_HIDDEN
    assert group.total_count == 10
    assert len(group.members) == 2


async def test_fetch_full_when_total_matches():
    users = [FakeUser(1, "alice"), FakeUser(2, "bob")]
    group = await _service(FakeClient(users=users, total=2)).fetch_group("@g")
    assert group.access_status is AccessStatus.FULL
    assert group.total_count == 2


async def test_thorough_fetch_finds_more_than_default():
    users = [
        FakeUser(1, "alice", "Alice"),
        FakeUser(2, "bob", "Bob"),
        FakeUser(3, "carol", "Carol"),
    ]
    # La pagination par défaut est plafonnée à 1 membre ; la recherche par lettre les remonte tous.
    normal = await _service(FakeClient(users=users, cap=1)).fetch_group("@g")
    assert len(normal.members) == 1

    thorough = await _service(FakeClient(users=users, cap=1)).fetch_group("@g", thorough=True)
    assert {m.user_id for m in thorough.members} == {1, 2, 3}  # dédupliqués


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


async def test_fetch_without_descriptions_leaves_bio_empty():
    users = [FakeUser(1, "alice", "Alice")]
    group = await _service(FakeClient(users=users)).fetch_group("@g")
    assert group.members[0].description is None


async def test_fetch_with_descriptions_uses_about_fetcher():
    users = [FakeUser(1, "alice", "Alice"), FakeUser(2, "bob", "Bob")]

    async def fake_about(client, user_id):
        return f"bio-{user_id}"

    service = TelegramService(
        1,
        "hash",
        "ignored",
        client_factory=lambda: FakeClient(users=users),
        about_fetcher=fake_about,
    )
    group = await service.fetch_group("@g", fetch_descriptions=True)
    bios = {m.user_id: m.description for m in group.members}
    assert bios == {1: "bio-1", 2: "bio-2"}
