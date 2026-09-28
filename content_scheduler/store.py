"""SQLite-backed post queue. No MCP code here, so it is easy to test."""
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.environ.get("CONTENT_DB", "posts.db")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_when(value: str) -> str:
    """Parse an ISO 8601 time into UTC. Naive times are treated as UTC."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            platform TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            scheduled_at TEXT,
            published_at TEXT,
            result TEXT,
            created_at TEXT NOT NULL
        )"""
    )
    return conn


def create(text: str, platform: str) -> dict:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO posts (text, platform, created_at) VALUES (?, ?, ?)",
            (text, platform, _now()),
        )
        new_id = cur.lastrowid
    return get(new_id)  # read after the transaction commits


def get(post_id: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        return dict(row) if row else None


def list_posts(status: str | None = None) -> list[dict]:
    with _conn() as c:
        if status:
            rows = c.execute(
                "SELECT * FROM posts WHERE status = ? ORDER BY id", (status,)
            ).fetchall()
        else:
            rows = c.execute("SELECT * FROM posts ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def schedule(post_id: int, when_iso: str) -> dict | None:
    when = parse_when(when_iso)
    with _conn() as c:
        c.execute(
            "UPDATE posts SET status='scheduled', scheduled_at=? "
            "WHERE id=? AND status IN ('draft','scheduled','failed')",
            (when, post_id),
        )
    return get(post_id)


def due(now_iso: str | None = None) -> list[dict]:
    now = now_iso or _now()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM posts WHERE status='scheduled' AND scheduled_at <= ? ORDER BY scheduled_at",
            (now,),
        ).fetchall()
        return [dict(r) for r in rows]


def mark(post_id: int, status: str, result: str = "") -> dict | None:
    published = _now() if status == "published" else None
    with _conn() as c:
        c.execute(
            "UPDATE posts SET status=?, result=?, published_at=? WHERE id=?",
            (status, result, published, post_id),
        )
    return get(post_id)


def delete(post_id: int) -> bool:
    with _conn() as c:
        cur = c.execute(
            "DELETE FROM posts WHERE id=? AND status != 'published'", (post_id,)
        )
        return cur.rowcount > 0
