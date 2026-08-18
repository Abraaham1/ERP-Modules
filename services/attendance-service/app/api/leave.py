import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, require_role
from app.core.config import settings
from app.core.logging import get_logger
from app.core.pagination import PaginationParams, pagination_params
from app.db.session import get_db
from app.models.enums import LeaveStatus, UserRole
from app.models.leave import LeaveRequest
from app.schemas.leave import (
    LeaveRequestCreate,
    LeaveRequestOut,
    LeaveReviewRequest,
    PaginatedLeaveRequests,
)

logger = get_logger("api.leave")

router = APIRouter(prefix="/leave", tags=["leave"])


async def _approved_days_used_this_year(
    db: AsyncSession, user_id: uuid.UUID, year: int
) -> int:
    result = await db.execute(
        select(LeaveRequest).where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status == LeaveStatus.APPROVED,
        )
    )
    requests = result.scalars().all()

    days_in_year = 0
    for req in requests:
        cur = req.start_date
        while cur <= req.end_date:
            if cur.year == year:
                days_in_year += 1
            cur = date.fromordinal(cur.toordinal() + 1)

    return days_in_year


@router.post("", response_model=LeaveRequestOut, status_code=status.HTTP_201_CREATED)
async def apply_for_leave(
    payload: LeaveRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    requested_days = (payload.end_date - payload.start_date).days + 1

    years_touched = {payload.start_date.year, payload.end_date.year}
    for year in years_touched:
        already_used = await _approved_days_used_this_year(db, current_user.id, year)
        days_in_this_request_for_year = sum(
            1
            for offset in range(requested_days)
            if (date.fromordinal(payload.start_date.toordinal() + offset)).year == year
        )
        if already_used + days_in_this_request_for_year > settings.max_leave_days_per_year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"This request would exceed the {settings.max_leave_days_per_year}-day "
                    f"leave allowance for {year} (already approved: {already_used} days)"
                ),
            )

    leave = LeaveRequest(
        user_id=current_user.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        reason=payload.reason,
        status=LeaveStatus.PENDING,
    )
    db.add(leave)
    await db.commit()
    await db.refresh(leave)

    logger.info(
        "Leave requested user_id=%s %s to %s (%s days)",
        current_user.id, payload.start_date, payload.end_date, requested_days,
    )
    return leave


@router.get("/me", response_model=PaginatedLeaveRequests)
async def get_my_leave_requests(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    pagination: PaginationParams = Depends(pagination_params),
):
    total = (
        await db.execute(
            select(func.count()).select_from(LeaveRequest).where(LeaveRequest.user_id == current_user.id)
        )
    ).scalar_one()

    result = await db.execute(
        select(LeaveRequest)
        .where(LeaveRequest.user_id == current_user.id)
        .order_by(LeaveRequest.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    items = result.scalars().all()

    return PaginatedLeaveRequests(
        items=list(items), total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get(
    "/inbox",
    response_model=PaginatedLeaveRequests,
    dependencies=[Depends(require_role(UserRole.HRM))],
)
async def get_leave_inbox(
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(pagination_params),
    status_filter: LeaveStatus = Query(
        LeaveStatus.PENDING, alias="status", description="Filter by status; defaults to pending only"
    ),
):
    total = (
        await db.execute(
            select(func.count()).select_from(LeaveRequest).where(LeaveRequest.status == status_filter)
        )
    ).scalar_one()

    result = await db.execute(
        select(LeaveRequest)
        .where(LeaveRequest.status == status_filter)
        .order_by(LeaveRequest.created_at.asc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    items = result.scalars().all()

    return PaginatedLeaveRequests(
        items=list(items), total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.post(
    "/{leave_id}/review",
    response_model=LeaveRequestOut,
    dependencies=[Depends(require_role(UserRole.HRM))],
)
async def review_leave_request(
    leave_id: uuid.UUID,
    payload: LeaveReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """HRM approves or rejects a pending leave request."""
    result = await db.execute(select(LeaveRequest).where(LeaveRequest.id == leave_id))
    leave = result.scalar_one_or_none()

    if leave is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

    if leave.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This request has already been {leave.status.value}",
        )

    leave.status = LeaveStatus.APPROVED if payload.approve else LeaveStatus.REJECTED
    leave.reviewed_by = current_user.id
    leave.reviewed_at = datetime.now(timezone.utc)
    leave.review_note = payload.review_note

    await db.commit()
    await db.refresh(leave)

    logger.info(
        "Leave %s user_id=%s reviewed_by=%s decision=%s",
        leave_id, leave.user_id, current_user.id, leave.status.value,
    )
    return leave
