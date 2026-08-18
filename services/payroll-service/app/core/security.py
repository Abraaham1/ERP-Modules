from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.models.enums import EmployeeType, UserRole


class TokenPayload(BaseModel):
    sub: str
    role: UserRole
    employee_type: EmployeeType | None = None
    exp: int
    type: str


def decode_token(token: str) -> TokenPayload | None:
    try:
        raw = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return TokenPayload(**raw)
    except JWTError:
        return None
    except ValueError:
        return None
