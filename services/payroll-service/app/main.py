from fastapi import FastAPI

from app.api import payroll
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="ERP Payroll Service", version="0.1.0")

app.include_router(payroll.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "payroll-service"}


@app.get("/")
async def root():
    return {"service": "payroll-service", "message": "Payroll service is running"}
