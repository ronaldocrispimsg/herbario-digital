import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.config import settings


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    last_error = None

    for _ in range(60):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            print("Database is ready")
            return
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(1)

    await engine.dispose()
    print(f"Database did not become ready: {last_error}", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
