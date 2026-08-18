import calendar
from datetime import date

from app.core.config import FIXED_SALARIES
from app.models.enums import EmployeeType


def get_fixed_salary(employee_type: EmployeeType) -> int:
    return FIXED_SALARIES[employee_type]


def is_weekend(d: date) -> bool:
    return d.weekday() in (5, 6)


def days_in_month(year: int, month: int) -> int:
    """
    Raw calendar day count (e.g. 31 for May 2026). Kept for the
    informational "days_in_month" field in the payroll response --
    NOT used in the deduction formula, see working_days_in_month.
    """
    return calendar.monthrange(year, month)[1]


def working_days_in_month(year: int, month: int) -> int:
    """
    Count of Mon-Fri days in the month, excluding Sat/Sun. This is
    the correct denominator for the deduction formula, since
    num_absents is only ever counted over working days (weekends
    can't be logged as absent in attendance-service). Using the raw
    calendar day count instead understates every deduction -- an
    employee absent on every working day could never lose 100% of
    salary, since working_days < calendar_days always.
    """
    num_days = calendar.monthrange(year, month)[1]
    return sum(
        1 for day in range(1, num_days + 1) if not is_weekend(date(year, month, day))
    )


def compute_deduction(total_salary: int, year: int, month: int, num_absents: int) -> float:
    """
    Deduction formula:
        D = (Total Salary / Working Days in Month) × No. of Absents

    `num_absents` is expected to already be the chargeable absent
    count -- attendance-service's over_allowance_absents, with the 3
    allowed absents per month already excluded.
    """
    wdim = working_days_in_month(year, month)
    return (total_salary / wdim) * num_absents


def compute_salary_so_far(total_salary: int, year: int, month: int, num_absents: int) -> float:
    """
    "Salary so far this month after deductions" -- resets to the full
    fixed salary at the start of each month.
    """
    deduction = compute_deduction(total_salary, year, month, num_absents)
    return round(total_salary - deduction, 2)


def is_first_of_month(d: date) -> bool:
    return d.day == 1