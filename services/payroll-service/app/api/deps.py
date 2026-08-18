import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.security import TokenPayload, decode_token
from app.models.enums import EmployeeType, UserRole

bearer_scheme = HTTPBearer()


class CurrentUser(BaseModel):
    id: uuid.UUID
    role: UserRole
    employee_type: EmployeeType | None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    payload: TokenPayload | None = decode_token(credentials.credentials)

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

    return CurrentUser(id=user_id, role=payload.role, employee_type=payload.employee_type)


def require_role(*allowed_roles: UserRole):
    async def _check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return _check
