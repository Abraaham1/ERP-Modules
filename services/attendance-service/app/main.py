from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import attendance, chart, leave
from app.core.logging import configure_logging
from app.db.session import Base, engine

from app.models import attendance as attendance_model 
from app.models import leave as leave_model 

from fastapi.middleware.cors import CORSMiddleware

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="ERP Attendance Service", version="0.1.0", lifespan=lifespan)

app.include_router(attendance.router)
app.include_router(chart.router)
app.include_router(leave.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://192.168.1.66:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "attendance-service"}


@app.get("/")
async def root():
    return {"service": "attendance-service", "message": "Attendance service is running"}

