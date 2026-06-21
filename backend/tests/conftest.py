from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session

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
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a session whose writes are always rolled back after each test.

    Pattern:
      - Outer BEGIN wraps the entire test.
      - An initial SAVEPOINT is opened before yielding the session.
      - An `after_transaction_end` listener re-opens the SAVEPOINT each time
        the session commits (which releases the previous one), so mid-test
        commits are visible within the session but never escape to the DB.
      - The outer transaction is rolled back in the finally block, leaving the
        in-memory DB clean for the next test.
    """
    async with engine.connect() as conn:
        trans = await conn.begin()
        await conn.begin_nested()  # open initial SAVEPOINT

        session = AsyncSession(bind=conn, expire_on_commit=False)

        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(sess: Session, transaction) -> None:
            # Re-open the SAVEPOINT after each commit so the next commit also
            # stays within the outer transaction boundary.
            if transaction.nested and not transaction._parent.nested:
                sess.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
