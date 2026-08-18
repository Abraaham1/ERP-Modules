import time
import uuid

import httpx
from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.models.enums import EmployeeType

logger = get_logger("client.auth")

AUTH_SERVICE_URL = "http://auth-service:8000"


async def fetch_employee_type(user_id: uuid.UUID, auth_header: str) -> EmployeeType:
    url = f"{AUTH_SERVICE_URL}/users/{user_id}"

    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers={"Authorization": auth_header})
    except httpx.RequestError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error("AUTH CALL FAILED (%.2fms) url=%s error=%s", elapsed_ms, url, exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not reach auth service")

    elapsed_ms = (time.perf_counter() - start) * 1000

    if response.status_code == status.HTTP_404_NOT_FOUND:
        logger.warning("AUTH CALL 404 (%.2fms) user_id=%s", elapsed_ms, user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if response.status_code != status.HTTP_200_OK:
        logger.error("AUTH CALL ERROR (%.2fms) status=%s body=%s", elapsed_ms, response.status_code, response.text)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Auth service returned an unexpected error")

    logger.info("AUTH CALL OK (%.2fms) user_id=%s", elapsed_ms, user_id)

    data = response.json()
    employee_type = data.get("employee_type")

    if employee_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user has no employee_type set and has no salary to calculate",
        )

    return EmployeeType(employee_type)
