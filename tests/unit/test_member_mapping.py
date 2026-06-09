"""Tests de l'extraction des champs d'un participant Telethon vers ``Member``."""

from __future__ import annotations

from pilottelega.core.telegram_service import TelegramService, format_last_seen


class FakeStatusOffline:
    def __init__(self, was_online):
        self.was_online = was_online


class FakeDate:
    def isoformat(self):
        return "2026-06-01T12:00:00"


class FakeUser:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.username = kwargs.get("username")
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.bot = kwargs.get("bot", False)
        self.premium = kwargs.get("premium", False)
        self.deleted = kwargs.get("deleted", False)
        self.status = kwargs.get("status")


def test_to_member_extracts_all_fields():
    user = FakeUser(
        id=42,
        username="neo",
        first_name="Thomas",
        last_name="Anderson",
        premium=True,
        status=FakeStatusOffline(FakeDate()),
    )
    member = TelegramService._to_member(user)
    assert member.user_id == 42
    assert member.username == "neo"
    assert member.first_name == "Thomas"
    assert member.last_name == "Anderson"
    assert member.display_name == "Thomas Anderson"
    assert member.is_premium is True
    assert member.is_bot is False
    assert member.is_deleted is False
    assert member.last_seen == "2026-06-01T12:00:00"


def test_to_member_bot_and_missing_fields():
    member = TelegramService._to_member(FakeUser(id=7, first_name="Botty", bot=True))
    assert member.is_bot is True
    assert member.username is None
    assert member.last_seen is None


class FakeStatusRecently:
    pass


def test_format_last_seen_readable_status():
    user = FakeUser(status=FakeStatusRecently())
    # Le nom de classe ne correspond pas au mapping → renvoie le nom brut.
    assert format_last_seen(user) == "FakeStatusRecently"


def test_format_last_seen_none():
    assert format_last_seen(FakeUser(status=None)) is None
