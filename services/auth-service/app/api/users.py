import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.hashing import hash_password
from app.core.logging import get_logger
from app.core.pagination import PaginationParams, pagination_params
from app.core.user_cache import get_cached_user, invalidate_cached_user, set_cached_user
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import PaginatedUsers, UserCreate, UserOut, UserUpdate

logger = get_logger("api.users")

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.HRM))],
)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        employee_type=payload.employee_type,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get(
    "",
    response_model=PaginatedUsers,
    dependencies=[Depends(require_role(UserRole.HRM))],
)
async def list_users(
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(pagination_params),
    include_inactive: bool = Query(
        False, description="If true, also include deactivated (soft-deleted) users."
    ),
):
    base_query = select(User)
    count_query = select(func.count()).select_from(User)

    if not include_inactive:
        base_query = base_query.where(User.is_active.is_(True))
        count_query = count_query.where(User.is_active.is_(True))

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(
        base_query.offset(pagination.offset)
        .limit(pagination.page_size)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return PaginatedUsers(
        items=list(users), total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.HRM and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    cached = await get_cached_user(user_id)
    if cached is not None:
        return UserOut(**cached)

    db_start = time.perf_counter()
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    db_elapsed_ms = (time.perf_counter() - db_start) * 1000
    logger.info("DB LOOKUP   (%.2fms)", db_elapsed_ms)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_out = UserOut.model_validate(user)
    await set_cached_user(user_id, user_out)
    return user_out


@router.patch(
    "/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_role(UserRole.HRM))],
)
async def update_user(user_id: uuid.UUID, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    await invalidate_cached_user(user_id)

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(UserRole.HRM))],
)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_active:
        return None

    user.is_active = False
    await db.commit()

    await invalidate_cached_user(user_id)

    return None