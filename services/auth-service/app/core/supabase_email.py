import secrets

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("core.supabase_email")


class SupabaseEmailError(Exception):
    pass


async def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """
    Sends the password reset email via Supabase Auth's built-in
    recovery flow -- used purely as an email delivery mechanism.

    IMPORTANT: this does NOT use Supabase's own reset token. We pass
    OUR reset link (containing OUR token, generated in auth.py) as the
    `redirect_to` target. Supabase's email template links to that URL
    -- our frontend's reset-password page reads OUR token from the
    query string we put in reset_link ourselves; any Supabase params
    appended after it are ignored.

    Requires a Supabase user to exist for this email (Supabase's
    recovery endpoint no-ops for unknown emails by design, to avoid
    email enumeration on their side too) -- so we create one via the
    admin API first if needed, using a random, never-used password
    since nobody ever logs into Supabase directly.
    """
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise SupabaseEmailError(
            "Supabase is not configured (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY missing)"
        )

    admin_headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Ensure a Supabase shadow user exists for this email. If it
        # already exists this returns an error we recognize and
        # ignore -- we don't need the response, just the user to
        # exist so the recovery email has somewhere to go.
        create_resp = await client.post(
            f"{settings.supabase_url}/auth/v1/admin/users",
            headers=admin_headers,
            json={
                "email": to_email,
                "email_confirm": True,
                "password": secrets.token_urlsafe(24),
            },
        )
        if create_resp.status_code not in (200, 201) and "already" not in create_resp.text.lower():
            logger.warning(
                "Supabase shadow user creation returned %s: %s",
                create_resp.status_code,
                create_resp.text[:200],
            )

        # Trigger Supabase's recovery email, pointed at OUR reset link.
        recover_resp = await client.post(
            f"{settings.supabase_url}/auth/v1/recover",
            headers={"apikey": settings.supabase_service_role_key, "Content-Type": "application/json"},
            json={"email": to_email, "options": {"redirect_to": reset_link}},
        )

    if recover_resp.status_code >= 400:
        logger.error(
            "Supabase recovery email failed status=%s body=%s",
            recover_resp.status_code,
            recover_resp.text[:300],
        )
        raise SupabaseEmailError(f"Supabase returned {recover_resp.status_code}")

    logger.info("Password reset email dispatched via Supabase to=%s", to_email)
