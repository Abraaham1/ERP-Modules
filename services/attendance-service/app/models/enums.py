import enum


class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    HRM = "hrm"


class EmployeeType(str, enum.Enum):
    SWE = "swe"
    ML_ENGINEER = "ml_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    SQA = "sqa"
    DB_ANALYST = "db_analyst"
    BACKEND_DEV = "backend_dev"
    FRONTEND_DEV = "frontend_dev"
    CTO = "cto"
    CPDO = "cpdo"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"


class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
