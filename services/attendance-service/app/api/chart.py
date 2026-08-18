from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.core.leave_lookup import get_approved_leave_dates
from app.core.rules import compute_monthly_totals
from app.db.session import get_db
from app.models.attendance import AttendanceRecord

router = APIRouter(prefix="/attendance/me/chart", tags=["attendance"])


class ChartSlice(BaseModel):
    label: str
    value: int


class ChartData(BaseModel):

    year: int
    month: int
    slices: list[ChartSlice]


@router.get("/{year}/{month}", response_model=ChartData)
async def get_my_chart_data(
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

    slices = [
        ChartSlice(label="Present", value=totals["present_days"]),
        ChartSlice(label="Absent", value=totals["raw_absent_days"]),
        ChartSlice(label="Half Day", value=totals["half_days"]),
        ChartSlice(label="Leave", value=totals["leave_days"]),
    ]

    return ChartData(year=year, month=month, slices=slices)
