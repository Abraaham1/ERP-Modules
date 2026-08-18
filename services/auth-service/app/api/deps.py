import time
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import decode_token
from app.core.user_cache import get_cached_user, set_cached_user
from app.db.session import get_db
from app.models.enums import EmployeeType, UserRole
from app.models.user import User
from app.schemas.user import UserOut

logger = get_logger("auth.deps")

bearer_scheme = HTTPBearer()


def _user_from_cache_dict(data: dict) -> User:

    user = User()
    user.id = uuid.UUID(data["id"])
    user.email = data["email"]
    user.full_name = data["full_name"]
    user.role = UserRole(data["role"])
    user.employee_type = EmployeeType(data["employee_type"]) if data["employee_type"] else None
    user.is_active = data["is_active"]
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)

    if payload is None or payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    cached = await get_cached_user(user_id)
    if cached is not None:
        user = _user_from_cache_dict(cached)
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        return user

    db_start = time.perf_counter()
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    db_elapsed_ms = (time.perf_counter() - db_start) * 1000
    logger.info("DB LOOKUP   (%.2fms)", db_elapsed_ms)

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    await set_cached_user(user.id, UserOut.model_validate(user))

    return user


def require_role(*allowed_roles: UserRole):

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return _check