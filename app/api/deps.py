"""Shared FastAPI dependencies."""

from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False, description="JWT access token from /auth/login")

_UNAUTHORISED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise _UNAUTHORISED

    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        if subject is None:
            raise _UNAUTHORISED
        user_id = int(subject)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise _UNAUTHORISED from None

    user = db.get(User, user_id)
    if user is None:
        raise _UNAUTHORISED
    return user
