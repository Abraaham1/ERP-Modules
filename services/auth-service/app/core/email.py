import smtplib
from email.message import EmailMessage

import anyio

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("core.email")


class EmailSendError(Exception):
    pass


def _build_message(to_email: str, reset_link: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "Reset your ERP Modules password"
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to_email

    msg.set_content(
        "Reset your password\n\n"
        "We received a request to reset your ERP Modules password. "
        f"Open this link to choose a new one:\n\n{reset_link}\n\n"
        "This link expires in 1 hour. If you didn't request this, you can ignore this email."
    )
    msg.add_alternative(
        f"""\
<div style="font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 480px; margin: 0 auto;">
  <h2 style="color: #4f46e5;">Reset your password</h2>
  <p>We received a request to reset your ERP Modules password. Click the button below:</p>
  <p style="margin: 24px 0;">
    <a href="{reset_link}"
       style="background: #4f46e5; color: white; padding: 12px 24px; border-radius: 8px;
              text-decoration: none; font-weight: 600; display: inline-block;">
      Reset Password
    </a>
  </p>
  <p style="color: #64748b; font-size: 14px;">This link expires in 1 hour.</p>
  <p style="color: #94a3b8; font-size: 12px;">
    If the button doesn't work, copy and paste this link into your browser:<br>
    {reset_link}
  </p>
</div>""",
        subtype="html",
    )
    return msg


def _send_sync(msg: EmailMessage) -> None:
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)


async def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """
    Sends the password reset email with OUR reset_link (containing our own
    one-time token) directly in the button href. No third-party auth
    provider is involved in generating, verifying, or redirecting this
    link -- see PasswordResetToken docstring. The mail server is used
    purely as a dumb transport.
    """
    if not settings.smtp_host:
        raise EmailSendError("SMTP is not configured")

    try:
        msg = _build_message(to_email, reset_link)
        await anyio.to_thread.run_sync(_send_sync, msg)
    except EmailSendError:
        raise
    except Exception as exc:
        logger.error("Failed to send password reset email to=%s err=%s", to_email, exc)
        raise EmailSendError(str(exc)) from exc

    logger.info("Password reset email dispatched to=%s", to_email)