"""Unit tests for JWT authentication."""

import pytest
from datetime import datetime, timedelta

from app.auth.jwt import AuthService, TokenData


class TestAuthService:
    """Tests for JWT authentication."""

    @pytest.fixture
    def auth_service(self):
        return AuthService()

    def test_create_access_token(self, auth_service):
        """Test token creation."""
        token = auth_service.create_access_token(
            user_id=123,
            telegram_id=456,
            username="testuser",
        )

        assert token.access_token is not None
        assert token.token_type == "bearer"
        assert token.expires_in > 0

    def test_verify_valid_token(self, auth_service):
        """Test verifying valid token."""
        token = auth_service.create_access_token(
            user_id=123,
            telegram_id=456,
            username="testuser",
        )

        token_data = auth_service.verify_token(token.access_token)

        assert token_data.user_id == 123
        assert token_data.telegram_id == 456
        assert token_data.username == "testuser"

    def test_verify_invalid_token(self, auth_service):
        """Test verifying invalid token."""
        with pytest.raises(Exception):
            auth_service.verify_token("invalid.token.here")

    def test_verify_expired_token(self, auth_service):
        """Test verifying expired token."""
        import jwt

        secret_key = auth_service.secret_key
        expired_time = datetime.utcnow() - timedelta(hours=1)

        expired_token = jwt.encode(
            {"user_id": 123, "telegram_id": 456, "exp": expired_time.timestamp()},
            secret_key,
            algorithm="HS256",
        )

        with pytest.raises(Exception):
            auth_service.verify_token(expired_token)

    def test_decode_token_unsafe(self, auth_service):
        """Test unsafe token decode."""
        token = auth_service.create_access_token(
            user_id=123,
            telegram_id=456,
        )

        token_data = auth_service.decode_token_unsafe(token.access_token)

        assert token_data is not None
        assert token_data.user_id == 123

    def test_create_token_from_telegram(self):
        """Test token creation from Telegram initData."""
        from app.auth.jwt import create_token_from_telegram

        init_data = "user=%7B%22id%22%3A123456%2C%22username%22%3A%22testuser%22%7D"

        token = create_token_from_telegram(init_data)

        assert token.access_token is not None
