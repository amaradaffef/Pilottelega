"""Tests d'intégration du cycle de login de ``TelegramService`` (T011 / US1).

Le client Telethon est injecté via ``client_factory`` : aucun réseau ni Telethon réel.
"""

from __future__ import annotations

from pilottelega.core.telegram_service import LoginStep, TelegramService


class SessionPasswordNeededError(Exception):
    """Réplique le nom de l'exception Telethon de 2FA (détectée par nom de classe)."""


class FakeClient:
    """Client Telethon minimal, contrôlable, pour les tests."""

    def __init__(self, *, authorized: bool = False, needs_password: bool = False) -> None:
        self._authorized = authorized
        self._needs_password = needs_password
        self.code_requests: list[str] = []
        self.connected = False

    async def connect(self) -> None:
        self.connected = True

    async def is_user_authorized(self) -> bool:
        return self._authorized

    async def send_code_request(self, phone: str) -> None:
        self.code_requests.append(phone)

    async def sign_in(
        self, phone: str | None = None, code: str | None = None, password: str | None = None
    ) -> None:
        if password is not None:
            self._authorized = True
            return
        if self._needs_password:
            raise SessionPasswordNeededError()
        self._authorized = True


def _service(client: FakeClient) -> TelegramService:
    return TelegramService(
        api_id=1, api_hash="hash", session_path="ignored", client_factory=lambda: client
    )


async def test_is_authorized_reflects_session():
    assert await _service(FakeClient(authorized=True)).is_authorized() is True
    assert await _service(FakeClient(authorized=False)).is_authorized() is False


async def test_start_login_sends_code():
    client = FakeClient()
    service = _service(client)
    await service.start_login("+33123456789")
    assert client.code_requests == ["+33123456789"]


async def test_submit_code_connected_without_2fa():
    client = FakeClient(needs_password=False)
    service = _service(client)
    await service.start_login("+33123456789")
    assert await service.submit_code("12345") is LoginStep.CONNECTED


async def test_submit_code_requires_password_with_2fa():
    client = FakeClient(needs_password=True)
    service = _service(client)
    await service.start_login("+33123456789")
    assert await service.submit_code("12345") is LoginStep.PASSWORD_REQUIRED


async def test_submit_password_completes_login():
    client = FakeClient(needs_password=True)
    service = _service(client)
    await service.start_login("+33123456789")
    await service.submit_code("12345")
    await service.submit_password("s3cret")
    assert await service.is_authorized() is True
