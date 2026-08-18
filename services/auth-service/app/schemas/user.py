import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import EmployeeType, UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.EMPLOYEE
    employee_type: EmployeeType | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    employee_type: EmployeeType | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    employee_type: EmployeeType | None
    is_active: bool
    created_at: datetime


class PaginatedUsers(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):

    sub: str  
    role: UserRole
    employee_type: EmployeeType | None = None
    exp: int
    type: str  
