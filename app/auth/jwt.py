"""JWT authentication module."""

import logging
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

ALGORITHM = "HS256"


class TokenData(BaseModel):
    user_id: int
    telegram_id: int
    username: Optional[str] = None
    exp: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class AuthService:
    """JWT authentication service."""

    def __init__(self):
        self.secret_key = settings.telegram.bot_token or "dev-secret-key"
        self.access_token_expire_minutes = 60 * 24 * 7

    def create_access_token(self, user_id: int, telegram_id: int, username: Optional[str] = None) -> Token:
        """Create JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode = {
            "user_id": user_id,
            "telegram_id": telegram_id,
            "username": username,
            "exp": expire.timestamp(),
        }

        access_token = jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
        )

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            return TokenData(
                user_id=payload.get("user_id"),
                telegram_id=payload.get("telegram_id"),
                username=payload.get("username"),
                exp=datetime.fromtimestamp(payload.get("exp", 0)),
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def decode_token_unsafe(self, token: str) -> Optional[TokenData]:
        """Decode token without verification (for logging)."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM], options={"verify_signature": False})
            return TokenData(
                user_id=payload.get("user_id"),
                telegram_id=payload.get("telegram_id"),
                username=payload.get("username"),
                exp=datetime.fromtimestamp(payload.get("exp", 0)),
            )
        except Exception:
            return None


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenData:
    """FastAPI dependency to get current user from JWT."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService()
    return auth_service.verify_token(credentials.credentials)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TokenData]:
    """FastAPI dependency for optional authentication."""
    if not credentials:
        return None

    try:
        auth_service = AuthService()
        return auth_service.verify_token(credentials.credentials)
    except HTTPException:
        return None


class WebSocketAuth:
    """WebSocket authentication helper."""

    @staticmethod
    async def authenticate(websocket, token: str) -> Optional[TokenData]:
        """Authenticate WebSocket connection."""
        if not token:
            return None

        try:
            auth_service = AuthService()
            return auth_service.verify_token(token)
        except Exception as e:
            logger.warning(f"WebSocket auth failed: {e}")
            return None


def create_token_from_telegram(init_data: str) -> Token:
    """Create JWT token from Telegram initData."""
    import urllib.parse
    
    auth_service = AuthService()
    
    try:
        params = urllib.parse.parse_qs(init_data)
        user_data = params.get('user', [{}])[0]
        
        if isinstance(user_data, str):
            import json
            user_data = json.loads(user_data)
        
        telegram_id = int(user_data.get('id', 0))
        username = user_data.get('username')
        
        return auth_service.create_access_token(
            user_id=telegram_id,
            telegram_id=telegram_id,
            username=username,
        )
    except Exception as e:
        logger.error(f"Failed to create token from initData: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid initData",
        )


auth_service = AuthService()
