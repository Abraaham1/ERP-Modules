import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import LeaveStatus


class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    reason: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def _validate_range(self) -> "LeaveRequestCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class LeaveReviewRequest(BaseModel):
    approve: bool
    review_note: str | None = Field(default=None, max_length=500)


class LeaveRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    start_date: date
    end_date: date
    reason: str
    status: LeaveStatus
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    review_note: str | None
    created_at: datetime

    @property
    def num_days(self) -> int:
        return (self.end_date - self.start_date).days + 1


class PaginatedLeaveRequests(BaseModel):
    items: list[LeaveRequestOut]
    total: int
    page: int
    page_size: int
