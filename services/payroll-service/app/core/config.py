from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.enums import EmployeeType

# Fixed salary per role, per spec ("Each role has fixed salary").
# Hardcoded here rather than DB-stored, per project decision -- changing
# a salary means editing this dict and redeploying, not an admin API call.
FIXED_SALARIES: dict[EmployeeType, int] = {
    EmployeeType.SWE: 150_000,
    EmployeeType.ML_ENGINEER: 180_000,
    EmployeeType.DEVOPS_ENGINEER: 160_000,
    EmployeeType.SQA: 120_000,
    EmployeeType.DB_ANALYST: 130_000,
    EmployeeType.BACKEND_DEV: 150_000,
    EmployeeType.FRONTEND_DEV: 140_000,
    EmployeeType.CTO: 400_000,
    EmployeeType.CPDO: 380_000,
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://erp_admin:erp_password@postgres:5432/payroll_db"

    redis_url: str = "redis://redis:6379/2"

    rabbitmq_url: str = "amqp://erp_admin:erp_password@rabbitmq:5672/"

    jwt_secret_key: str = "admin123"
    jwt_algorithm: str = "HS256"

    attendance_service_url: str = "http://attendance-service:8000"

    payroll_reset_day: int = 1


settings = Settings()
