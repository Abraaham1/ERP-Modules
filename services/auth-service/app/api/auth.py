import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.hashing import hash_password, verify_password
from app.core.logging import get_logger
from app.core.rate_limit import check_login_rate_limit, reset_login_rate_limit
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.supabase_email import send_password_reset_email
from app.core.user_cache import invalidate_cached_user
from app.db.session import get_db
from app.models.user import PasswordResetToken, RefreshToken, User
from app.schemas.user import (
    AccessToken,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
    UserOut,
)

logger = get_logger("api.auth")

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


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Always returns 202 regardless of whether the email exists -- this
    prevents the endpoint from being usable to enumerate registered
    emails. Our own reset token is generated here; Supabase is only
    used in the background to deliver the email, so the request
    doesn't block on that network call either.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is not None and user.is_active:
        raw_token = secrets.token_urlsafe(32)

        reset_row = PasswordResetToken(
            user_id=user.id,
            token=raw_token,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.password_reset_token_expire_minutes),
        )
        db.add(reset_row)
        await db.commit()

        reset_link = f"{settings.frontend_base_url}/reset-password?token={raw_token}"

        async def _send():
            try:
                await send_password_reset_email(user.email, reset_link)
            except Exception:
                logger.exception("Failed to send password reset email via Supabase to=%s", user.email)

        background_tasks.add_task(_send)
        logger.info("Password reset requested user_id=%s", user.id)
    else:
        logger.info("Password reset requested for unknown/inactive email (no email sent)")

    return {"detail": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == payload.token)
    )
    reset_row = result.scalar_one_or_none()

    if reset_row is None or reset_row.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or already-used reset link")

    if reset_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This reset link has expired")

    user_result = await db.execute(select(User).where(User.id == reset_row.user_id))
    user = user_result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account not found or inactive")

    user.hashed_password = hash_password(payload.new_password)
    reset_row.used = True

    # Revoke all existing refresh tokens -- a password reset should end
    # every other logged-in session, not just let the old password's
    # sessions keep working.
    revoke_result = await db.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False))
    )
    for token_row in revoke_result.scalars().all():
        token_row.revoked = True

    await db.commit()
    await invalidate_cached_user(user.id)

    logger.info("Password reset completed user_id=%s", user.id)
    return None
