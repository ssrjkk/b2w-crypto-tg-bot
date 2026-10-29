"""Роли WebSocket-подключения считает сервер, а не клиент.

До правки любой клиент, не приславший user_id, попадал в админский канал
(`connect()` трактовал отсутствующего пользователя как админа), а `is_admin`
брался прямо из тела сообщения."""

import json
from types import SimpleNamespace

import pytest

from app.api import websocket as ws


class FakeWebSocket:
    def __init__(self, frames):
        self._frames = list(frames)
        self.accepted = False
        self.sent = []

    async def accept(self):
        self.accepted = True

    async def receive_text(self):
        if not self._frames:
            raise ws.WebSocketDisconnect()
        return self._frames.pop(0)

    async def send_text(self, text):
        self.sent.append(json.loads(text))

    @property
    def client_state(self):
        return SimpleNamespace(name="CONNECTED")


@pytest.fixture
def manager():
    fresh = ws.ConnectionManager()
    original = ws.manager
    ws.manager = fresh
    yield fresh
    ws.manager = original


@pytest.fixture
def with_admins(monkeypatch):
    monkeypatch.setattr(ws, "settings", SimpleNamespace(telegram=SimpleNamespace(admin_ids=[7])))


async def _run(manager, frames):
    socket = FakeWebSocket(frames)
    await ws.websocket_endpoint(socket)
    return socket


async def test_anonymous_socket_is_not_admin(manager):
    socket = await _run(manager, [json.dumps({"type": "ping"})])

    assert socket.sent == [{"type": "pong"}]
    assert manager._admin_connections == set()


async def test_admin_role_comes_from_server_side_list(manager, with_admins):
    socket = FakeWebSocket([])
    session = ws._Session()

    await ws._authenticate(socket, session, {"type": "auth", "user_id": 7})

    assert session.is_admin is True
    assert socket.sent == [{"type": "auth_confirmed", "user_id": 7}]
    assert manager._admin_connections == {socket}
    assert 7 in manager.get_connected_users()

    manager.disconnect(socket, session.user_id, session.is_admin)
    assert manager._admin_connections == set()
    assert manager.get_connection_count() == 0


async def test_client_claimed_admin_is_ignored(manager, with_admins):
    socket = FakeWebSocket([])
    session = ws._Session()

    await ws._authenticate(socket, session, {"type": "auth", "user_id": 42, "is_admin": True})

    assert session.is_admin is False
    assert manager._admin_connections == set()


async def test_malformed_json_gets_an_error_frame(manager):
    socket = await _run(manager, ["{not json"])

    assert socket.sent == [{"type": "error", "message": "Invalid JSON"}]
