import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import AttendanceStatus


class AttendanceLogRequest(BaseModel):
    """Employees log their own attendance for a given work day."""

    work_date: date
    status: AttendanceStatus


class AttendanceRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    work_date: date
    status: AttendanceStatus
    created_at: datetime


class MonthlyStats(BaseModel):
    """
    Aggregated view for a single employee/month.
      - Approved leave days are excluded from the count entirely --
        neither present nor absent, no salary impact.
      - Every 3 half-days convert into 1 additional absent, but ONLY
        when half-days are exactly a multiple of 3 remainder-wise --
        i.e. 1 or 2 leftover half-days never round up to an absent.
      - There is no automatic "N free absents" buffer: every day that
        isn't present, isn't approved leave, and isn't folded into a
        half-day conversion is chargeable for payroll purposes.
    """

    user_id: uuid.UUID
    year: int
    month: int = Field(ge=1, le=12)

    present_days: int
    raw_absent_days: int
    half_days: int
    leave_days: int

    # Half-days converted into absents via the 3-half-days-per-absent rule.
    half_day_converted_absents: int

    # raw_absent_days + half_day_converted_absents
    total_absents: int

    # Equal to total_absents -- kept as a separate field for
    # payroll-service compatibility (it reads this field name).
    over_allowance_absents: int

    @model_validator(mode="after")
    def _compute_derived(self) -> "MonthlyStats":
        return self


class PaginatedAttendance(BaseModel):
    items: list[AttendanceRecordOut]
    total: int
    page: int
    page_size: int
