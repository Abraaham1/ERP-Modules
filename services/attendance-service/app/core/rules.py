import calendar
from datetime import date

from app.core.config import settings
from app.models.enums import AttendanceStatus


def is_weekend(d: date) -> bool:
    return d.weekday() in (5, 6)


def working_days_in_month(year: int, month: int) -> list[date]:
    num_days = calendar.monthrange(year, month)[1]
    return [
        d
        for day in range(1, num_days + 1)
        if not is_weekend(d := date(year, month, day))
    ]


def working_days_elapsed(year: int, month: int, as_of: date | None = None) -> list[date]:
    as_of = as_of or date.today()
    return [d for d in working_days_in_month(year, month) if d <= as_of]


def compute_monthly_totals(
    statuses_by_date: dict[date, AttendanceStatus],
    year: int,
    month: int,
    approved_leave_dates: set[date] | None = None,
    as_of: date | None = None,
) -> dict:

    approved_leave_dates = approved_leave_dates or set()

    elapsed_days = [
        d for d in working_days_elapsed(year, month, as_of) if d not in approved_leave_dates
    ]
    leave_days_this_month = sum(
        1 for d in working_days_elapsed(year, month, as_of) if d in approved_leave_dates
    )

    present_days = sum(
        1 for d in elapsed_days if statuses_by_date.get(d) == AttendanceStatus.PRESENT
    )
    half_days = sum(
        1 for d in elapsed_days if statuses_by_date.get(d) == AttendanceStatus.HALF_DAY
    )
    explicitly_logged_absent = sum(
        1 for d in elapsed_days if statuses_by_date.get(d) == AttendanceStatus.ABSENT
    )
    unlogged_days = sum(1 for d in elapsed_days if d not in statuses_by_date)

    raw_absent_days = explicitly_logged_absent + unlogged_days

    half_day_converted_absents = half_days // settings.half_days_per_absent

    total_absents = raw_absent_days + half_day_converted_absents

    return {
        "present_days": present_days,
        "raw_absent_days": raw_absent_days,
        "half_days": half_days,
        "half_day_converted_absents": half_day_converted_absents,
        "leave_days": leave_days_this_month,
        "total_absents": total_absents,
        "over_allowance_absents": total_absents,
    }
