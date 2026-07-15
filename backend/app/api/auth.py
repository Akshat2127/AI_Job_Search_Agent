import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.identity import AuthSession, User
from backend.app.schemas.auth import BrowserSessionOut, LoginRequest, RegisterRequest, SessionOut, UserOut
from backend.app.security.auth import create_session, get_current_user, hash_token, normalize_email, password_hash

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


@router.post("/browser-login", response_model=BrowserSessionOut)
def browser_login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> BrowserSessionOut:
    user = db.execute(select(User).where(User.email == normalize_email(str(payload.email)))).scalar_one_or_none()
    if user is None or user.password_hash is None or not password_hash.verify(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token, _ = create_session(db, user)
    csrf_token = secrets.token_urlsafe(32)
    max_age = settings.session_ttl_hours * 3600
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=max_age,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite="strict",
        path="/",
    )
    return BrowserSessionOut(expires_in=max_age, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    cookie_token = request.cookies.get(settings.session_cookie_name)
    authorization = request.headers.get("Authorization", "")
    bearer_token = authorization[7:] if authorization.lower().startswith("bearer ") else None
    current_token = cookie_token or bearer_token
    statement = select(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
    if current_token is not None:
        statement = statement.where(AuthSession.token_hash == hash_token(current_token))
    sessions = db.execute(statement).scalars()
    now = datetime.now(UTC)
    for session in sessions:
        session.revoked_at = now
    db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")
