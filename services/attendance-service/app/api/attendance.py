import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.core.leave_lookup import get_approved_leave_dates
from app.core.logging import get_logger
from app.core.pagination import PaginationParams, pagination_params
from app.core.rules import compute_monthly_totals, is_weekend
from app.db.session import get_db
from app.models.attendance import AttendanceRecord
from app.schemas.attendance import (
    AttendanceLogRequest,
    AttendanceRecordOut,
    MonthlyStats,
    PaginatedAttendance,
)

logger = get_logger("api.attendance")

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("", response_model=AttendanceRecordOut, status_code=status.HTTP_201_CREATED)
async def log_attendance(
    payload: AttendanceLogRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):

    if payload.work_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot log attendance for a future date"
        )

    if is_weekend(payload.work_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot log attendance on a weekend (Sat/Sun are off)",
        )

    result = await db.execute(
        select(AttendanceRecord).where(
            AttendanceRecord.user_id == current_user.id,
            AttendanceRecord.work_date == payload.work_date,
        )
    )
    existing = result.scalar_one_or_none()

    if existing is not None:
        existing.status = payload.status
        await db.commit()
        await db.refresh(existing)
        logger.info("Updated attendance user_id=%s date=%s status=%s", current_user.id, payload.work_date, payload.status.value)
        return existing

    record = AttendanceRecord(
        user_id=current_user.id, work_date=payload.work_date, status=payload.status
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    logger.info("Logged attendance user_id=%s date=%s status=%s", current_user.id, payload.work_date, payload.status.value)
    return record


@router.get("/me", response_model=PaginatedAttendance)
async def get_my_attendance(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    pagination: PaginationParams = Depends(pagination_params),
    year: int | None = Query(None, description="Filter to a specific year"),
    month: int | None = Query(None, ge=1, le=12, description="Filter to a specific month (requires year)"),
):
    query = select(AttendanceRecord).where(AttendanceRecord.user_id == current_user.id)
    count_query = select(func.count()).select_from(AttendanceRecord).where(
        AttendanceRecord.user_id == current_user.id
    )

    if year is not None:
        query = query.where(extract("year", AttendanceRecord.work_date) == year)
        count_query = count_query.where(extract("year", AttendanceRecord.work_date) == year)
        if month is not None:
            query = query.where(extract("month", AttendanceRecord.work_date) == month)
            count_query = count_query.where(extract("month", AttendanceRecord.work_date) == month)

    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(
        query.order_by(AttendanceRecord.work_date.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    records = result.scalars().all()

    return PaginatedAttendance(
        items=list(records), total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/me/stats/{year}/{month}", response_model=MonthlyStats)
async def get_my_monthly_stats(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if not (1 <= month <= 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="month must be 1-12")

    result = await db.execute(
        select(AttendanceRecord.work_date, AttendanceRecord.status).where(
            AttendanceRecord.user_id == current_user.id,
            extract("year", AttendanceRecord.work_date) == year,
            extract("month", AttendanceRecord.work_date) == month,
        )
    )
    statuses_by_date = {row[0]: row[1] for row in result.all()}

    leave_dates = await get_approved_leave_dates(db, current_user.id, year, month)
    totals = compute_monthly_totals(statuses_by_date, year, month, approved_leave_dates=leave_dates)
    return MonthlyStats(user_id=current_user.id, year=year, month=month, **totals)


@router.get(
    "/user/{user_id}/stats/{year}/{month}",
    response_model=MonthlyStats,
)
async def get_user_monthly_stats(
    user_id: uuid.UUID,
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):

    from app.models.enums import UserRole

    if current_user.role != UserRole.HRM and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if not (1 <= month <= 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="month must be 1-12")

    result = await db.execute(
        select(AttendanceRecord.work_date, AttendanceRecord.status).where(
            AttendanceRecord.user_id == user_id,
            extract("year", AttendanceRecord.work_date) == year,
            extract("month", AttendanceRecord.work_date) == month,
        )
    )
    statuses_by_date = {row[0]: row[1] for row in result.all()}

    leave_dates = await get_approved_leave_dates(db, user_id, year, month)
    totals = compute_monthly_totals(statuses_by_date, year, month, approved_leave_dates=leave_dates)
    return MonthlyStats(user_id=user_id, year=year, month=month, **totals)
