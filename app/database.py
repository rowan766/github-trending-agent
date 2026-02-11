import aiosqlite
import os
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trending.db")


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pushed_repos (
                repo_name TEXT PRIMARY KEY,
                first_seen DATE,
                last_pushed DATE,
                push_count INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date DATE UNIQUE,
                report_html TEXT,
                project_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def is_recently_pushed(repo_name: str, dedup_days: int = 7) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cutoff = (date.today() - timedelta(days=dedup_days)).isoformat()
        cursor = await db.execute(
            "SELECT 1 FROM pushed_repos WHERE repo_name = ? AND last_pushed >= ?",
            (repo_name, cutoff)
        )
        return await cursor.fetchone() is not None


async def mark_pushed(repo_names: list[str]):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        for name in repo_names:
            await db.execute("""
                INSERT INTO pushed_repos (repo_name, first_seen, last_pushed, push_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(repo_name) DO UPDATE SET
                    last_pushed = ?, push_count = push_count + 1
            """, (name, today, today, today))
        await db.commit()


async def save_report(report_html: str, project_count: int):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO daily_reports (report_date, report_html, project_count) VALUES (?, ?, ?)",
            (today, report_html, project_count)
        )
        await db.commit()


async def get_latest_report() -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM daily_reports ORDER BY report_date DESC LIMIT 1")
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_report_history(limit: int = 30) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, report_date, project_count, created_at FROM daily_reports ORDER BY report_date DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in await cursor.fetchall()]
