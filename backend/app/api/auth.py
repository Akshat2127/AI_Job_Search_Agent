from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.identity import AuthSession, User
from backend.app.schemas.auth import LoginRequest, RegisterRequest, SessionOut, UserOut
from backend.app.security.auth import create_session, get_current_user, normalize_email, password_hash

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    email = normalize_email(str(payload.email))
    if db.execute(select(User.id).where(User.email == email)).scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(email=email, password_hash=password_hash.hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=SessionOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> SessionOut:
    user = db.execute(select(User).where(User.email == normalize_email(str(payload.email)))).scalar_one_or_none()
    if user is None or user.password_hash is None or not password_hash.verify(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token, _ = create_session(db, user)
    return SessionOut(
        access_token=token, expires_in=settings.session_ttl_hours * 3600, user=UserOut.model_validate(user)
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    sessions = db.execute(
        select(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
    ).scalars()
    now = datetime.now(UTC)
    for session in sessions:
        session.revoked_at = now
    db.commit()
