import time
import uuid

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("client.attendance")


async def fetch_monthly_absences(
    user_id: uuid.UUID, year: int, month: int, auth_header: str
) -> int:

    url = f"{settings.attendance_service_url}/attendance/user/{user_id}/stats/{year}/{month}"

    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers={"Authorization": auth_header})
    except httpx.RequestError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error("ATTENDANCE CALL FAILED (%.2fms) url=%s error=%s", elapsed_ms, url, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach attendance service",
        )

    elapsed_ms = (time.perf_counter() - start) * 1000

    if response.status_code == status.HTTP_403_FORBIDDEN:
        logger.warning("ATTENDANCE CALL FORBIDDEN (%.2fms) user_id=%s", elapsed_ms, user_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view attendance for this user")

    if response.status_code != status.HTTP_200_OK:
        logger.error(
            "ATTENDANCE CALL ERROR (%.2fms) status=%s body=%s",
            elapsed_ms, response.status_code, response.text,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Attendance service returned an unexpected error",
        )

    logger.info("ATTENDANCE CALL OK (%.2fms) user_id=%s year=%s month=%s", elapsed_ms, user_id, year, month)

    data = response.json()
    return data["over_allowance_absents"]