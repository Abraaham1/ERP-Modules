import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import EmployeeType


class SalarySummary(BaseModel):
    user_id: uuid.UUID
    employee_type: EmployeeType
    year: int
    month: int

    fixed_salary: float
    days_in_month: int
    num_absents: int

    deduction: float
    salary_so_far: float

    computed_at: datetime
