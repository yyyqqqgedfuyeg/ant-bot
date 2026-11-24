"""Async SQLite WAL connection management and short transaction helpers."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from weakref import WeakKeyDictionary

import aiosqlite

from .config import get_db_path, is_memory_db
from .schema import apply_schema

BUSY_TIMEOUT_MS = 5000
_CONNECT_TIMEOUT_SECONDS = BUSY_TIMEOUT_MS / 1000.0

_loop_locks: WeakKeyDictionary[asyncio.AbstractEventLoop, dict[Path, asyncio.Lock]] = (
    WeakKeyDictionary()
)


def _get_write_lock(resolved_path: Path) -> asyncio.Lock:
    """Return a per-event-loop, per-database-path asyncio lock for write serialization."""
    loop = asyncio.get_running_loop()
    locks_for_loop = _loop_locks.setdefault(loop, {})
    lock = locks_for_loop.get(resolved_path)
    if lock is None:
        lock = asyncio.Lock()
        locks_for_loop[resolved_path] = lock
    return lock


async def _configure_connection(conn: aiosqlite.Connection, resolved_path: Path) -> None:
    """Enforce WAL mode, synchronous=NORMAL, and busy_timeout=5000 on every connection."""
    conn.row_factory = aiosqlite.Row
    await conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    if not is_memory_db(resolved_path):
        cursor = await conn.execute("PRAGMA journal_mode")
        row = await cursor.fetchone()
        await cursor.close()
        current_mode = str(row[0]).lower() if row is not None else ""
        if current_mode != "wal":
            mode_cursor = await conn.execute("PRAGMA journal_mode = WAL")
            await mode_cursor.close()
    await conn.execute("PRAGMA synchronous = NORMAL")


async def _open_connection(resolved_path: Path) -> aiosqlite.Connection:
    if not is_memory_db(resolved_path):
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(
        resolved_path,
        timeout=_CONNECT_TIMEOUT_SECONDS,
        isolation_level=None,
    )
    try:
        await _configure_connection(conn, resolved_path)
    except BaseException:
        await conn.close()
        raise
    return conn


@asynccontextmanager
async def get_connection(
    db_path: str | Path | None = None,
) -> AsyncIterator[aiosqlite.Connection]:
    """Yield a configured async SQLite connection (WAL, NORMAL, busy_timeout=5000)."""
    resolved = get_db_path(db_path)
    conn = await _open_connection(resolved)
    try:
        yield conn
    finally:
        await conn.close()


@asynccontextmanager
async def transaction(
    db_path: str | Path | None = None,
) -> AsyncIterator[aiosqlite.Connection]:
    """Run a short SQLite IMMEDIATE write transaction with automatic commit/rollback."""
    resolved = get_db_path(db_path)
    lock = _get_write_lock(resolved)
    async with lock:
        conn = await _open_connection(resolved)
        try:
            await conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except BaseException:
                if conn.in_transaction:
                    await conn.execute("ROLLBACK")
                raise
            else:
                if conn.in_transaction:
                    await conn.execute("COMMIT")
        finally:
            await conn.close()


async def init_db(db_path: str | Path | None = None) -> Path:
    """Initialize SQLite schema and default user_settings idempotently."""
    resolved = get_db_path(db_path)
    async with transaction(resolved) as conn:
        await apply_schema(conn)
    return resolved
