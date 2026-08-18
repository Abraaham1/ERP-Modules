
import asyncio
import os

from sqlalchemy import select

from app.core.hashing import hash_password
from app.db.session import AsyncSessionLocal, Base, engine
from app.models.enums import UserRole
from app.models.user import User

SEED_EMAIL = os.environ.get("SEED_EMAIL", "admin@erp.com")
SEED_PASSWORD = os.environ.get("SEED_PASSWORD", "admin123")
SEED_NAME = os.environ.get("SEED_NAME", "System Admin")


async def seed_admin() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == SEED_EMAIL))
        existing = result.scalar_one_or_none()

        if existing is not None:
            print(f"User '{SEED_EMAIL}' already exists (role={existing.role.value}). Nothing to do.")
            return

        user = User(
            email=SEED_EMAIL,
            full_name=SEED_NAME,
            hashed_password=hash_password(SEED_PASSWORD),
            role=UserRole.HRM,
            employee_type=None,
        )
        db.add(user)
        await db.commit()

        print(f"Created HRM user:")
        print(f"  email:    {SEED_EMAIL}")
        print(f"  password: {SEED_PASSWORD}")
        print(f"  role:     hrm")
        print()
        print("Log in via POST /auth/login with these credentials to get your token.")


if __name__ == "__main__":
    asyncio.run(seed_admin())