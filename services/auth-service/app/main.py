from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth, users
from app.core.logging import configure_logging
from app.db.session import Base, engine

from app.models import user  

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="ERP Auth Service", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth-service"}


@app.get("/")
async def root():
    return {"service": "auth-service", "message": "Auth service is running"}