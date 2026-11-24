"""Unit tests for backend.shared.db and scripts.lint_arch."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import aiosqlite
import pytest

from backend.shared.db import (
    get_connection,
    get_db_path,
    init_db,
    set_db_path,
    transaction,
)
from scripts.lint_arch import (
    ALL_ERROR_MSG,
    ERROR_MSG,
    check_backend_architecture,
    check_source_imports,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_TABLES = {
    "bots",
    "user_settings",
    "messages",
    "event_inbox",
    "shared_memories",
    "device_push_tokens",
    "push_records",
}

EXPECTED_INDEXES = {
    "idx_messages_bot_seq",
    "idx_event_inbox_due",
    "idx_event_inbox_bot",
    "idx_push_records_status",
}


async def test_init_db_creates_schema_wal_and_default_settings(tmp_path: Path) -> None:
    db_file = tmp_path / "nested" / "ant_bot.db"
    resolved = await init_db(db_file)
    assert resolved == db_file.resolve()
    assert db_file.exists()

    async with get_connection(db_file) as conn:
        mode_row = await (await conn.execute("PRAGMA journal_mode")).fetchone()
        sync_row = await (await conn.execute("PRAGMA synchronous")).fetchone()
        timeout_row = await (await conn.execute("PRAGMA busy_timeout")).fetchone()
        assert mode_row is not None and str(mode_row[0]).lower() == "wal"
        assert sync_row is not None and int(sync_row[0]) == 1  # NORMAL
        assert timeout_row is not None and int(timeout_row[0]) == 5000

        table_rows = await (
            await conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        ).fetchall()
        assert {row["name"] for row in table_rows} == EXPECTED_TABLES

        index_rows = await (
            await conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
            )
        ).fetchall()
        assert {row["name"] for row in index_rows} == EXPECTED_INDEXES

        settings_rows = await (await conn.execute("SELECT * FROM user_settings")).fetchall()
        assert len(settings_rows) == 1
        row = settings_rows[0]
        assert row["id"] == 1
        assert row["timezone"] == "Asia/Shanghai"
        assert row["global_default_model"] == "gemini-4-Hydrogen"
        assert row["quiet_hours_enabled"] == 0
        assert row["quiet_hours_start"] == "23:00"
        assert row["quiet_hours_end"] == "08:00"
        assert row["updated_at"]

    # Mutate settings and verify re-running init_db is idempotent and preserves user edits.
    async with transaction(db_file) as conn:
        await conn.execute(
            "UPDATE user_settings SET timezone = ?, quiet_hours_enabled = 1 WHERE id = 1",
            ("America/Los_Angeles",),
        )

    await init_db(db_file)
    async with get_connection(db_file) as conn:
        updated = await (await conn.execute("SELECT * FROM user_settings WHERE id = 1")).fetchone()
        assert updated is not None
        assert updated["timezone"] == "America/Los_Angeles"
        assert updated["quiet_hours_enabled"] == 1


async def test_shared_memories_value_max_length_120_and_constraints(tmp_path: Path) -> None:
    db_file = tmp_path / "constraints.db"
    await init_db(db_file)

    ok_ascii = "a" * 120
    ok_unicode = "中" * 120
    async with transaction(db_file) as conn:
        await conn.execute(
            """
            INSERT INTO shared_memories (id, memory_key, value, updated_by, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("m-ascii", "ascii_120", ok_ascii, "supervisor", "2026-11-24T08:00:00Z"),
        )
        await conn.execute(
            """
            INSERT INTO shared_memories (id, memory_key, value, updated_by, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("m-unicode", "unicode_120", ok_unicode, "supervisor", "2026-11-24T08:00:00Z"),
        )

    with pytest.raises(aiosqlite.IntegrityError):
        async with transaction(db_file) as conn:
            await conn.execute(
                """
                INSERT INTO shared_memories (id, memory_key, value, updated_by, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("m-too-long", "too_long_ascii", "a" * 121, "supervisor", "2026-11-24T08:00:00Z"),
            )

    with pytest.raises(aiosqlite.IntegrityError):
        async with transaction(db_file) as conn:
            await conn.execute(
                """
                INSERT INTO shared_memories (id, memory_key, value, updated_by, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "m-too-long-u",
                    "too_long_unicode",
                    "中" * 121,
                    "supervisor",
                    "2026-11-24T08:00:00Z",
                ),
            )

    # Verify transaction rolled back cleanly when failing after an earlier statement.
    with pytest.raises(aiosqlite.IntegrityError):
        async with transaction(db_file) as conn:
            await conn.execute(
                """
                INSERT INTO bots (
                    id, name, purpose_one_liner, avatar_config_json,
                    default_model, is_preset, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "bot-rollback",
                    "Rollback Bot",
                    "Should roll back",
                    "{}",
                    "gemini-4-Hydrogen",
                    0,
                    "2026-11-24T08:00:00Z",
                    "2026-11-24T08:00:00Z",
                ),
            )
            await conn.execute(
                """
                INSERT INTO user_settings (id, updated_at)
                VALUES (2, '2026-11-24T08:00:00Z')
                """
            )

    async with get_connection(db_file) as conn:
        bot_row = await (
            await conn.execute("SELECT id FROM bots WHERE id = 'bot-rollback'")
        ).fetchone()
        assert bot_row is None


async def test_db_path_resolution_supports_env_and_setter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_db = tmp_path / "env_based.db"
    configured_db = tmp_path / "configured.db"
    explicit_db = tmp_path / "explicit.db"

    try:
        set_db_path(configured_db)
        assert get_db_path() == configured_db.resolve()

        monkeypatch.setenv("ANT_BOT_DB_PATH", str(env_db))
        assert get_db_path() == env_db.resolve()
        assert get_db_path(explicit_db) == explicit_db.resolve()

        await init_db()
        assert env_db.exists()
    finally:
        set_db_path(None)


async def test_concurrent_coroutine_writes_succeed_without_database_locked(
    tmp_path: Path,
) -> None:
    db_file = tmp_path / "concurrent.db"
    await init_db(db_file)

    total_writers = 50

    async def write_message(seq: int) -> None:
        async with transaction(db_file) as conn:
            await conn.execute(
                """
                INSERT INTO messages (
                    id, client_temp_id, bot_id, sender_type, content, seq, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"msg-{seq}",
                    f"tmp-{seq}",
                    "supervisor",
                    "user" if seq % 2 == 0 else "bot",
                    f"concurrent payload {seq}",
                    seq,
                    "2026-11-24T08:00:00Z",
                ),
            )

    async def read_count() -> int:
        async with get_connection(db_file) as conn:
            row = await (await conn.execute("SELECT COUNT(*) FROM messages")).fetchone()
            assert row is not None
            return int(row[0])

    tasks = [write_message(i) for i in range(total_writers)]
    readers = [read_count() for _ in range(15)]
    await asyncio.gather(*tasks, *readers)

    final_count = await read_count()
    assert final_count == total_writers


def test_lint_arch_passes_on_current_repo() -> None:
    assert check_backend_architecture(REPO_ROOT) == []
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "lint_arch.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "[ARCH][OK]" in proc.stdout


@pytest.mark.parametrize(
    ("rel_file", "snippet"),
    [
        (
            "backend/features/chat/internal/service.py",
            "from backend.features.bots.internal.repo import BotRepo\n",
        ),
        (
            "backend/features/chat/internal/service.py",
            "import backend.tools.features.memory.internal.store\n",
        ),
        (
            "backend/features/chat/__init__.py",
            "from backend.shared.db.internal.schema import apply_schema\n",
        ),
        (
            "backend/main.py",
            "from backend.features.bots import internal\n",
        ),
        (
            "backend/features/chat/internal/service.py",
            "from ...bots.internal.repo import BotRepo\n",
        ),
        (
            "backend/shared/cache/__init__.py",
            "from ..db.internal.config import get_db_path\n",
        ),
        (
            "backend/features/chat/internal/service.py",
            "from ...bots import internal\n",
        ),
    ],
)
def test_lint_arch_rejects_cross_module_internal_imports(
    tmp_path: Path, rel_file: str, snippet: str
) -> None:
    backend_root = tmp_path / "backend"
    file_path = tmp_path / rel_file
    errors = check_source_imports(
        snippet,
        file_path=file_path,
        backend_root=backend_root,
        repo_root=tmp_path,
    )
    assert len(errors) == 1
    assert ERROR_MSG in errors[0]


@pytest.mark.parametrize(
    ("rel_file", "snippet"),
    [
        (
            "backend/features/bots/__init__.py",
            "from .internal.repo import BotRepo\n__all__ = ['BotRepo']\n",
        ),
        (
            "backend/features/bots/internal/service.py",
            "from .repo import BotRepo\nfrom ..internal.models import Bot\n",
        ),
        (
            "backend/features/chat/internal/service.py",
            "from backend.features.bots import BotRepo\nfrom backend.shared.db import transaction\n",
        ),
        (
            "backend/features/chat/internal/pb.py",
            "from google.protobuf.internal import wire_format\n",
        ),
    ],
)
def test_lint_arch_allows_same_module_and_public_imports(
    tmp_path: Path, rel_file: str, snippet: str
) -> None:
    backend_root = tmp_path / "backend"
    file_path = tmp_path / rel_file
    errors = check_source_imports(
        snippet,
        file_path=file_path,
        backend_root=backend_root,
        repo_root=tmp_path,
    )
    assert errors == []


def test_lint_arch_cli_enforces_internal_and_dunder_all_on_temp_repo(tmp_path: Path) -> None:
    (tmp_path / "backend" / "features" / "alpha" / "internal").mkdir(parents=True)
    (tmp_path / "backend" / "features" / "beta" / "internal").mkdir(parents=True)
    (tmp_path / "backend" / "tools" / "features" / "reminder" / "internal").mkdir(parents=True)
    (tmp_path / "backend" / "shared" / "cache" / "internal").mkdir(parents=True)

    # alpha/__init__.py intentionally omits __all__
    (tmp_path / "backend" / "features" / "alpha" / "__init__.py").write_text(
        "from .internal.svc import run\n", encoding="utf-8"
    )
    (tmp_path / "backend" / "features" / "alpha" / "internal" / "svc.py").write_text(
        "from backend.features.beta.internal.secret import TOKEN\n", encoding="utf-8"
    )
    (tmp_path / "backend" / "features" / "beta" / "__init__.py").write_text(
        "__all__ = []\n", encoding="utf-8"
    )
    (tmp_path / "backend" / "features" / "beta" / "internal" / "secret.py").write_text(
        "TOKEN = 'x'\n", encoding="utf-8"
    )
    # tool __init__.py intentionally omits __all__
    (tmp_path / "backend" / "tools" / "features" / "reminder" / "__init__.py").write_text(
        "def ping():\n    return 'pong'\n", encoding="utf-8"
    )
    # shared __init__.py intentionally omits __all__
    (tmp_path / "backend" / "shared" / "cache" / "__init__.py").write_text(
        "VALUE = 1\n", encoding="utf-8"
    )

    errors = check_backend_architecture(tmp_path)
    assert any(ERROR_MSG in err for err in errors)
    assert sum(1 for err in errors if ALL_ERROR_MSG in err) == 3

    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "lint_arch.py"), "--root", str(tmp_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert ERROR_MSG in proc.stderr
    assert ALL_ERROR_MSG in proc.stderr
