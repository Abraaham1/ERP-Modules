import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import CurrentUser, get_current_user, require_role
from app.clients.attendance_client import fetch_monthly_absences
from app.clients.auth_client import fetch_employee_type
from app.core.logging import get_logger
from app.core.payroll_rules import compute_deduction, days_in_month, get_fixed_salary
from app.models.enums import UserRole
from app.schemas.payroll import SalarySummary

logger = get_logger("api.payroll")

router = APIRouter(prefix="/payroll", tags=["payroll"])


async def _build_salary_summary(
    user_id: uuid.UUID,
    employee_type,
    year: int,
    month: int,
    auth_header: str,
) -> SalarySummary:
    fixed_salary = get_fixed_salary(employee_type)
    num_absents = await fetch_monthly_absences(user_id, year, month, auth_header)
    deduction = compute_deduction(fixed_salary, year, month, num_absents)

    return SalarySummary(
        user_id=user_id,
        employee_type=employee_type,
        year=year,
        month=month,
        fixed_salary=fixed_salary,
        days_in_month=days_in_month(year, month),
        num_absents=num_absents,
        deduction=round(deduction, 2),
        salary_so_far=round(fixed_salary - deduction, 2),
        computed_at=datetime.now(timezone.utc),
    )


@router.get("/me", response_model=SalarySummary)
async def get_my_salary(
    request: Request,
    year: int | None = None,
    month: int | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.employee_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your account has no employee_type set and has no salary to calculate",
        )

    today = date.today()
    target_year = year or today.year
    target_month = month or today.month

    auth_header = request.headers.get("Authorization", "")

    summary = await _build_salary_summary(
        current_user.id, current_user.employee_type, target_year, target_month, auth_header
    )
    logger.info(
        "Salary summary user_id=%s %s-%s salary_so_far=%s",
        current_user.id, target_year, target_month, summary.salary_so_far,
    )
    return summary


@router.get(
    "/user/{user_id}",
    response_model=SalarySummary,
    dependencies=[Depends(require_role(UserRole.HRM))],
)
async def get_user_salary(
    user_id: uuid.UUID,
    request: Request,
    year: int | None = None,
    month: int | None = None,
):
    """HRM-only: view any employee's salary summary."""
    today = date.today()
    target_year = year or today.year
    target_month = month or today.month

    auth_header = request.headers.get("Authorization", "")

    employee_type = await fetch_employee_type(user_id, auth_header)

    summary = await _build_salary_summary(
        user_id, employee_type, target_year, target_month, auth_header
    )
    logger.info(
        "Salary summary (HRM view) user_id=%s %s-%s salary_so_far=%s",
        user_id, target_year, target_month, summary.salary_so_far,
    )
    return summary
