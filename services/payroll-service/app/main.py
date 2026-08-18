from fastapi import FastAPI

from app.api import payroll
from app.core.logging import configure_logging
from fastapi.middleware.cors import CORSMiddleware

configure_logging()

app = FastAPI(title="ERP Payroll Service", version="0.1.0")

app.include_router(payroll.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "payroll-service"}


@app.get("/")
async def root():
    return {"service": "payroll-service", "message": "Payroll service is running"}
