"""
RabbitMQ wrapper for the password-reset email flow.

Topology (declared idempotently on startup / first use):

    erp.events                          topic exchange, durable
    auth.email_worker                   durable queue, bound to routing key
                                         "auth.password_reset_requested"
    auth.email_worker.retry             durable queue, x-message-ttl backoff,
                                         dead-letters back into erp.events
    erp.events.dlx                      fanout exchange, durable
    auth.email_worker.dlq               durable queue bound to the DLX

Why this exists: the forgot-password endpoint used to send the email inline
via FastAPI's BackgroundTasks, which runs in the same process as the API. A
slow or unreachable SMTP server would tie up that worker process, and a
failed send only produced a log line -- nothing retried it. Publishing an
event and letting a separate worker process consume it means:

  - the API request returns as soon as the token is saved, never waiting
    on SMTP
  - a stuck/slow SMTP call blocks the email worker only, never the API
  - a failed send is retried automatically (with backoff) instead of
    silently dying, and after MAX_DELIVERY_ATTEMPTS lands in a DLQ for
    manual inspection instead of being lost

This is intentionally scoped to just this one flow -- the rest of the
system (payroll <-> attendance <-> auth) is synchronous request/response
by requirement, not by oversight, so it isn't queued.
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("core.rabbitmq")

EVENTS_EXCHANGE = "erp.events"
DLX_EXCHANGE = "erp.events.dlx"

# Redeliver a failed message this many times before it's routed to the DLQ.
MAX_DELIVERY_ATTEMPTS = 3

# Delay before a failed message is retried (milliseconds).
RETRY_DELAY_MS = 10_000

_connection: AbstractRobustConnection | None = None
_publish_channel: aio_pika.abc.AbstractChannel | None = None


async def get_connection() -> AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        logger.info("RabbitMQ connection established")
    return _connection


async def _get_publish_channel() -> aio_pika.abc.AbstractChannel:
    global _publish_channel
    if _publish_channel is None or _publish_channel.is_closed:
        conn = await get_connection()
        _publish_channel = await conn.channel(publisher_confirms=True)
        await _publish_channel.declare_exchange(
            EVENTS_EXCHANGE, ExchangeType.TOPIC, durable=True
        )
    return _publish_channel


async def publish_event(routing_key: str, payload: dict[str, Any]) -> None:
    """
    Publish an event to the erp.events topic exchange, with publisher
    confirms enabled so we know the broker actually accepted it.

    Callers should treat this as best-effort and not let a publish failure
    block the underlying DB transaction that triggered the event -- catch
    and log, don't raise, if the caller shouldn't fail the HTTP request
    just because the broker publish hiccuped.
    """
    channel = await _get_publish_channel()
    exchange = await channel.get_exchange(EVENTS_EXCHANGE)

    body = json.dumps(payload, default=str).encode()
    message = aio_pika.Message(
        body=body,
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )

    await exchange.publish(message, routing_key=routing_key)
    logger.info("EVENT PUBLISHED routing_key=%s", routing_key)


async def close() -> None:
    global _connection, _publish_channel
    if _publish_channel is not None and not _publish_channel.is_closed:
        await _publish_channel.close()
    if _connection is not None and not _connection.is_closed:
        await _connection.close()
    _connection = None
    _publish_channel = None


Handler = Callable[[dict[str, Any]], Awaitable[None]]


async def consume(
    queue_name: str,
    routing_keys: list[str],
    handler: Handler,
    prefetch_count: int = 10,
) -> None:
    """
    Declare `queue_name`, bind it to `routing_keys` on erp.events, and consume
    forever, calling `handler(payload)` for each message.

    Failed messages go to a per-queue retry queue with a TTL (backoff delay);
    when the TTL expires they're dead-lettered back into the original queue
    for another attempt. After MAX_DELIVERY_ATTEMPTS the message is rejected
    without requeue and lands in "<queue_name>.dlq" for manual inspection --
    it is never silently dropped and never redelivered forever.

    Intended to run in a standalone worker process (see app/worker.py), not
    inside the FastAPI request/response cycle.
    """
    conn = await get_connection()
    channel = await conn.channel()
    await channel.set_qos(prefetch_count=prefetch_count)

    events_exchange = await channel.declare_exchange(
        EVENTS_EXCHANGE, ExchangeType.TOPIC, durable=True
    )
    dlx_exchange = await channel.declare_exchange(
        DLX_EXCHANGE, ExchangeType.FANOUT, durable=True
    )

    dlq_name = f"{queue_name}.dlq"
    dlq = await channel.declare_queue(dlq_name, durable=True)
    await dlq.bind(dlx_exchange)

    retry_exchange_name = f"{queue_name}.retry"
    retry_exchange = await channel.declare_exchange(
        retry_exchange_name, ExchangeType.DIRECT, durable=True
    )

    queue = await channel.declare_queue(
        queue_name,
        durable=True,
        arguments={"x-dead-letter-exchange": DLX_EXCHANGE},
    )
    for key in routing_keys:
        await queue.bind(events_exchange, routing_key=key)

    # Retry queue: holds messages for RETRY_DELAY_MS, then TTL expiry dead-letters
    # them back into erp.events with their original routing key, which routes them
    # straight back into `queue` since it's still bound to that key.
    retry_queue_name = f"{queue_name}.retry"
    retry_queue = await channel.declare_queue(
        retry_queue_name,
        durable=True,
        arguments={
            "x-dead-letter-exchange": EVENTS_EXCHANGE,
            "x-message-ttl": RETRY_DELAY_MS,
        },
    )
    await retry_queue.bind(retry_exchange, routing_key=queue_name)

    logger.info(
        "Consumer ready queue=%s routing_keys=%s dlq=%s retry_delay_ms=%s",
        queue_name, routing_keys, dlq_name, RETRY_DELAY_MS,
    )

    async def _on_message(message: AbstractIncomingMessage) -> None:
        death_count = 0
        if message.headers and "x-death" in message.headers:
            for death in message.headers["x-death"]:
                if death.get("queue") in (queue_name, retry_queue_name):
                    death_count += int(death.get("count", 0))

        try:
            payload = json.loads(message.body)
        except json.JSONDecodeError:
            logger.error("Undecodable message on queue=%s, sending to DLQ", queue_name)
            await message.reject(requeue=False)  # -> DLX -> dlq
            return

        payload["_routing_key"] = message.routing_key

        try:
            await handler(payload)
        except Exception:
            if death_count + 1 >= MAX_DELIVERY_ATTEMPTS:
                logger.exception(
                    "Handler failed on queue=%s after %s attempts, routing to DLQ",
                    queue_name, death_count + 1,
                )
                await message.reject(requeue=False)  # -> DLX -> dlq
            else:
                logger.warning(
                    "Handler failed on queue=%s attempt=%s, retrying in %sms",
                    queue_name, death_count + 1, RETRY_DELAY_MS,
                )
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=message.body,
                        content_type=message.content_type,
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        headers=message.headers,
                    ),
                    routing_key=retry_queue_name,
                )
                await message.ack()  # remove from main queue; it now lives in retry queue
            return

        await message.ack()

    await queue.consume(_on_message)

    # Block forever; the worker process's entrypoint awaits this.
    await asyncio.Future()
