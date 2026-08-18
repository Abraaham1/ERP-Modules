import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings
from app.models.enums import EmployeeType, UserRole
from app.schemas.user import TokenPayload


def _create_token(
    user_id: uuid.UUID,
    role: UserRole,
    employee_type: EmployeeType | None,
    expires_delta: timedelta,
    token_type: str,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "employee_type": employee_type.value if employee_type else None,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "type": token_type,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(
    user_id: uuid.UUID, role: UserRole, employee_type: EmployeeType | None
) -> str:
    return _create_token(
        user_id,
        role,
        employee_type,
        timedelta(minutes=settings.access_token_expire_minutes),
        token_type="access",
    )


def create_refresh_token(
    user_id: uuid.UUID, role: UserRole, employee_type: EmployeeType | None
) -> str:
    return _create_token(
        user_id,
        role,
        employee_type,
        timedelta(days=settings.refresh_token_expire_days),
        token_type="refresh",
    )


def decode_token(token: str) -> TokenPayload | None:
    try:
        raw = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return TokenPayload(**raw)
    except JWTError:
        return None
    except ValueError:
        return None
