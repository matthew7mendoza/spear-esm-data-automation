"""
Database configuration & session management
"""

import os
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./spear_automation.db")

async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session_creator = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def init_db_tables() -> None:
    """
    Build database table schema if missing on startup
    """

    async with async_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    provides temporary db connection for request,
    safely closes when finished
    """

    async with async_session_creator() as session:
        yield session