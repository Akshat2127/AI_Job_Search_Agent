import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.identity import AuthSession, User

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: User) -> tuple[str, AuthSession]:
    token = secrets.token_urlsafe(48)
    session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(hours=settings.session_ttl_hours),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return token, session


def _not_expired(value: datetime) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value > datetime.now(UTC)


def _user_from_bearer(db: Session, token: str) -> User | None:
    session = db.execute(select(AuthSession).where(AuthSession.token_hash == hash_token(token))).scalar_one_or_none()
    if session is None or session.revoked_at is not None or not _not_expired(session.expires_at):
        return None
    user = db.get(User, session.user_id)
    return user if user is not None and user.is_active else None


def _development_user(db: Session, request: Request) -> User:
    if request.client is not None and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Development authentication is localhost-only")
    email = normalize_email(settings.development_user_email)
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        user = User(email=email, password_hash=None)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is not None:
        user = _user_from_bearer(db, credentials.credentials)
        if user is not None:
            return user
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired access token")
    if settings.auth_mode == "development":
        return _development_user(db, request)
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
