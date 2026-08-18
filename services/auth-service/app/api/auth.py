import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.hashing import verify_password
from app.core.rate_limit import check_login_rate_limit, reset_login_rate_limit
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.session import get_db
from app.models.user import RefreshToken, User
from app.schemas.user import AccessToken, LoginRequest, RefreshRequest, TokenPair, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    allowed = await check_login_rate_limit(payload.email.lower())
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    await reset_login_rate_limit(payload.email.lower())

    access_token = create_access_token(user.id, user.role, user.employee_type)
    refresh_token_str = create_refresh_token(user.id, user.role, user.employee_type)

    refresh_token_row = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(refresh_token_row)
    await db.commit()

    return TokenPair(access_token=access_token, refresh_token=refresh_token_str)


@router.post("/refresh", response_model=AccessToken)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_payload = decode_token(payload.refresh_token)

    if token_payload is None or token_payload.type != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
    )
    stored_token = result.scalar_one_or_none()

    if stored_token is None or stored_token.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or unknown")

    if stored_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user_result = await db.execute(select(User).where(User.id == uuid.UUID(token_payload.sub)))
    user = user_result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    new_access_token = create_access_token(user.id, user.role, user.employee_type)
    return AccessToken(access_token=new_access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == payload.refresh_token)
    )
    stored_token = result.scalar_one_or_none()

    if stored_token is not None:
        stored_token.revoked = True
        await db.commit()

    return None


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
