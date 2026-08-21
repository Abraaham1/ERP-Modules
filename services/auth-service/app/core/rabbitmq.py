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

MAX_DELIVERY_ATTEMPTS = 3

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
                await message.ack() 
            return

        await message.ack()

    await queue.consume(_on_message)

    await asyncio.Future()
