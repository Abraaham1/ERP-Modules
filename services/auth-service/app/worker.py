"""
Standalone consumer process for the password-reset email flow. Runs as its
own container (see docker-compose.yml: auth-email-worker) so a slow or
failing SMTP send never blocks the auth-service API's event loop.

Run with: python -m app.worker
"""

import asyncio

from app.core.logging import configure_logging, get_logger
from app.core.rabbitmq import consume
from app.events.handlers import handle_password_reset_requested
from app.events.routing_keys import PASSWORD_RESET_REQUESTED

configure_logging()
logger = get_logger("worker")

QUEUE_NAME = "auth.email_worker"


async def dispatch(payload: dict) -> None:
    routing_key = payload.get("_routing_key")
    if routing_key != PASSWORD_RESET_REQUESTED:
        logger.warning("No handler registered for routing_key=%s, dropping", routing_key)
        return
    await handle_password_reset_requested(payload)


async def main() -> None:
    logger.info("auth-service email worker starting")
    await consume(
        queue_name=QUEUE_NAME,
        routing_keys=[PASSWORD_RESET_REQUESTED],
        handler=dispatch,
    )


if __name__ == "__main__":
    asyncio.run(main())
