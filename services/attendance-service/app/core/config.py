from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://erp_admin:erp_password@postgres:5432/attendance_db"

    # Redis
    redis_url: str = "redis://redis:6379/1"

    # RabbitMQ
    rabbitmq_url: str = "amqp://erp_admin:erp_password@rabbitmq:5672/"
    
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    half_days_per_absent: int = 3

    max_leave_days_per_year: int = 15


settings = Settings()
