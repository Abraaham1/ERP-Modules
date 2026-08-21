from app.core.email import send_password_reset_email
from app.core.logging import get_logger

logger = get_logger("events.handlers")


async def handle_password_reset_requested(payload: dict) -> None:
    email = payload["email"]
    reset_link = payload["reset_link"]
    await send_password_reset_email(email, reset_link)
