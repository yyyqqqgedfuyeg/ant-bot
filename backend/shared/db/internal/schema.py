"""SQLite schema DDL and default seed data for ant-bot backend."""

from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS bots (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        purpose_one_liner TEXT NOT NULL,
        avatar_config_json TEXT NOT NULL,
        default_model TEXT NOT NULL,
        is_preset INTEGER NOT NULL DEFAULT 0 CHECK (is_preset IN (0, 1)),
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        timezone TEXT NOT NULL DEFAULT 'Asia/Shanghai',
        global_default_model TEXT NOT NULL DEFAULT 'gemini-4-Hydrogen',
        quiet_hours_enabled INTEGER NOT NULL DEFAULT 0 CHECK (quiet_hours_enabled IN (0, 1)),
        quiet_hours_start TEXT NOT NULL DEFAULT '23:00',
        quiet_hours_end TEXT NOT NULL DEFAULT '08:00',
        updated_at DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        client_temp_id TEXT UNIQUE,
        bot_id TEXT NOT NULL,
        sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'bot')),
        content TEXT,
        attachments_json TEXT,
        reply_to_msg_id TEXT,
        model_used TEXT,
        seq INTEGER NOT NULL,
        created_at DATETIME NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_messages_bot_seq
    ON messages (bot_id, seq ASC)
    """,
    """
    CREATE TABLE IF NOT EXISTS event_inbox (
        id TEXT PRIMARY KEY,
        target_bot_id TEXT NOT NULL,
        prompt TEXT NOT NULL,
        schedule_type TEXT NOT NULL CHECK (schedule_type IN ('once', 'cron')),
        cron_expr TEXT,
        user_timezone TEXT NOT NULL,
        next_run_at_utc DATETIME NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'done', 'cancelled')),
        claimed_at_utc DATETIME,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_event_inbox_due
    ON event_inbox (status, next_run_at_utc)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_event_inbox_bot
    ON event_inbox (target_bot_id, status)
    """,
    """
    CREATE TABLE IF NOT EXISTS shared_memories (
        id TEXT PRIMARY KEY,
        memory_key TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL CHECK (length(value) <= 120),
        updated_by TEXT NOT NULL,
        updated_at DATETIME NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS device_push_tokens (
        device_id TEXT PRIMARY KEY,
        expo_push_token TEXT NOT NULL,
        platform TEXT NOT NULL CHECK (platform IN ('ios', 'android', 'web')),
        updated_at DATETIME NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS push_records (
        id TEXT PRIMARY KEY,
        bot_id TEXT NOT NULL,
        bot_name TEXT NOT NULL,
        message_ids_json TEXT NOT NULL,
        preview_text TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('queued', 'sent', 'skipped_online', 'failed')),
        created_at DATETIME NOT NULL,
        sent_at DATETIME
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_push_records_status
    ON push_records (status, created_at)
    """,
)

_SEED_USER_SETTINGS_SQL = """
INSERT OR IGNORE INTO user_settings (
    id,
    timezone,
    global_default_model,
    quiet_hours_enabled,
    quiet_hours_start,
    quiet_hours_end,
    updated_at
) VALUES (
    1,
    'Asia/Shanghai',
    'gemini-4-Hydrogen',
    0,
    '23:00',
    '08:00',
    ?
)
"""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def apply_schema(conn: aiosqlite.Connection) -> None:
    """Create all server tables, indexes, and default user_settings idempotently."""
    for statement in SCHEMA_STATEMENTS:
        await conn.execute(statement)
    await conn.execute(_SEED_USER_SETTINGS_SQL, (_utc_now_iso(),))
