"""History service — SQLite-backed analysis history."""
from __future__ import annotations
import aiosqlite
import os
import json
from datetime import datetime, timezone
from app.models.schemas import HistoryEntry

def _get_db_path() -> str:
    """Use /tmp on Vercel (read-only filesystem), local path otherwise."""
    if os.environ.get("VERCEL"):
        return "/tmp/satquery.db"
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "satquery.db")

DB_PATH = _get_db_path()


async def init_db():
    """Initialize the history database."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                image_name TEXT,
                query TEXT NOT NULL,
                answer TEXT NOT NULL,
                intent TEXT,
                confidence REAL,
                mode TEXT DEFAULT 'demo'
            )
        """)
        await db.commit()


async def add_entry(
    image_name: str,
    query: str,
    answer: str,
    intent: str,
    confidence: float,
    mode: str = "demo",
) -> int:
    """Add an analysis to history. Returns the entry ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO analysis_history (timestamp, image_name, query, answer, intent, confidence, mode)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                image_name,
                query,
                answer,
                intent,
                confidence,
                mode,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_history(limit: int = 50) -> list[HistoryEntry]:
    """Get recent analysis history."""
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM analysis_history ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [
            HistoryEntry(
                id=row["id"],
                timestamp=row["timestamp"],
                image_name=row["image_name"] or "",
                query=row["query"],
                answer=row["answer"],
                intent=row["intent"] or "",
                confidence=row["confidence"] or 0,
                mode=row["mode"] or "demo",
            )
            for row in rows
        ]


async def get_entry(entry_id: int) -> HistoryEntry | None:
    """Get a specific history entry."""
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM analysis_history WHERE id = ?",
            (entry_id,),
        )
        row = await cursor.fetchone()
        if row:
            return HistoryEntry(
                id=row["id"],
                timestamp=row["timestamp"],
                image_name=row["image_name"] or "",
                query=row["query"],
                answer=row["answer"],
                intent=row["intent"] or "",
                confidence=row["confidence"] or 0,
                mode=row["mode"] or "demo",
            )
        return None
