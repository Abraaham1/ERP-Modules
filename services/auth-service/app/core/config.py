from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://erp_admin:erp_password@postgres:5432/auth_db"

    redis_url: str = "redis://redis:6379/0"

    rabbitmq_url: str = "amqp://erp_admin:erp_password@rabbitmq:5672/"

    jwt_secret_key: str = "ABD123"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 1

    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 300  

    # Password reset
    password_reset_token_expire_minutes: int = 60
    frontend_base_url: str = "http://localhost:5173"

    # Supabase -- used ONLY to deliver the reset email via Supabase
    # Auth's built-in recovery flow. Our own auth (login, JWT issuing,
    # RBAC) is completely separate and never talks to Supabase.
    supabase_url: str = ""
    supabase_service_role_key: str = ""

settings = Settings()
