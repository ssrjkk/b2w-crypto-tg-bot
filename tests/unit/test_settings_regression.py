"""Regression tests for configuration and error-contract bugs.

Covers two fixed bugs:
1. DatabaseSettings.path had no validation alias and matched the system
   PATH environment variable case-insensitively, so the sqlite URL became
   the whole PATH string on machines without DATABASE__PATH.
2. The global 500 handler called logger.error with unsupported kwargs and
   masked every unhandled exception with a TypeError instead of the JSON
   error contract.
"""

from fastapi.testclient import TestClient

from app.api.main import create_app
from app.config.settings import DatabaseSettings

DEFAULT_DB_PATH = "data/platform.db"
ERROR_CONTRACT = {"error": "Internal server error", "code": "INTERNAL_ERROR"}


def _clear_db_env(monkeypatch):
    monkeypatch.delenv("DATABASE__PATH", raising=False)
    monkeypatch.delenv("DB_PATH", raising=False)


def test_path_variable_is_not_captured_as_database_path(monkeypatch):
    """The system PATH must never leak into the database path."""
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("PATH", "/sentinel/bin:/usr/bin")
    assert DatabaseSettings().path == DEFAULT_DB_PATH


def test_database__path_env_is_read(monkeypatch):
    """The compose/.env variable (DATABASE__PATH) drives the setting."""
    _clear_db_env(monkeypatch)
    url = "postgresql://user:pass@db:5432/platform"
    monkeypatch.setenv("DATABASE__PATH", url)
    assert DatabaseSettings().path == url


def test_db_path_env_is_read(monkeypatch):
    """The README systemd example (DB_PATH) drives the setting too."""
    _clear_db_env(monkeypatch)
    monkeypatch.setenv("DB_PATH", "/opt/coursework/bot.db")
    assert DatabaseSettings().path == "/opt/coursework/bot.db"


def test_unhandled_error_answers_with_json_contract(monkeypatch):
    """A 500 must return the JSON error contract, never a masked TypeError."""
    _clear_db_env(monkeypatch)
    # The default sqlite file does not exist in a fresh checkout, so the
    # route deterministically fails with OperationalError.
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.get("/api/subscription/status/1")
    assert response.status_code == 500
    assert response.json() == ERROR_CONTRACT
