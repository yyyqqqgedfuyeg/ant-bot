"""Database path configuration for ant-bot backend."""

from __future__ import annotations

import os
from pathlib import Path

DB_PATH_ENV_VAR = "ANT_BOT_DB_PATH"
DEFAULT_DB_PATH = Path(__file__).resolve().parents[4] / "data" / "ant_bot.db"

_configured_db_path: Path | None = None


def is_memory_db(path: str | Path) -> bool:
    """Return True if the path refers to an in-memory SQLite database."""
    return str(path) == ":memory:"


def _normalize_path(raw_path: str | Path) -> Path:
    if is_memory_db(raw_path):
        return Path(":memory:")
    return Path(raw_path).expanduser().resolve()


def set_db_path(db_path: str | Path | None) -> Path | None:
    """Configure or clear the process-wide fallback database path."""
    global _configured_db_path
    _configured_db_path = None if db_path is None else _normalize_path(db_path)
    return _configured_db_path


def get_db_path(db_path: str | Path | None = None) -> Path:
    """Resolve the active SQLite database path.

    Priority: explicit argument > ANT_BOT_DB_PATH env var > set_db_path() > default path.
    """
    if db_path is not None:
        return _normalize_path(db_path)
    env_path = os.environ.get(DB_PATH_ENV_VAR, "").strip()
    if env_path:
        return _normalize_path(env_path)
    if _configured_db_path is not None:
        return _configured_db_path
    return DEFAULT_DB_PATH
