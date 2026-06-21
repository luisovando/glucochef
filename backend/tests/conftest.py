import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
import app.models  # noqa: F401 — registers all ORM models with Base.metadata

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncSession:
    """
    Yields a session whose writes are always rolled back after each test.

    Uses a connection-level SAVEPOINT so that calling session.commit() inside
    a test does not permanently persist data. After the test the outer
    transaction is rolled back, leaving the in-memory DB clean for the next test.
    """
    async with engine.connect() as conn:
        trans = await conn.begin()
        # Wrap in a SAVEPOINT so nested commits don't escape to the outer transaction.
        await conn.begin_nested()

        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
