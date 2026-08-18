import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rules import working_days_in_month
from app.models.enums import LeaveStatus
from app.models.leave import LeaveRequest


async def get_approved_leave_dates(
    db: AsyncSession, user_id: uuid.UUID, year: int, month: int
) -> set[date]:
    result = await db.execute(
        select(LeaveRequest).where(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status == LeaveStatus.APPROVED,
        )
    )
    approved_requests = result.scalars().all()

    month_working_days = set(working_days_in_month(year, month))
    leave_dates: set[date] = set()

    for req in approved_requests:
        cur = req.start_date
        while cur <= req.end_date:
            if cur in month_working_days:
                leave_dates.add(cur)
            cur = date.fromordinal(cur.toordinal() + 1)

    return leave_dates
