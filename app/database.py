import aiosqlite
import json
import os
from datetime import date, timedelta
from app.auth import hash_password

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trending.db")

DEFAULT_TECH_STACK = [
    {"name": "AI/LLM", "weight": 10, "enabled": True, "preset": True},
    {"name": "Vue.js", "weight": 9, "enabled": True, "preset": True},
    {"name": "React", "weight": 8, "enabled": True, "preset": True},
    {"name": "FastAPI", "weight": 9, "enabled": True, "preset": True},
    {"name": "Three.js", "weight": 7, "enabled": True, "preset": True},
    {"name": "Cesium", "weight": 7, "enabled": True, "preset": True},
    {"name": "Docker", "weight": 6, "enabled": True, "preset": True},
    {"name": "n8n", "weight": 6, "enabled": True, "preset": True},
    {"name": "Dify", "weight": 7, "enabled": True, "preset": True},
]

PRESET_TECH_TYPES = [
    "AI/LLM", "Vue.js", "React", "Angular", "Svelte", "Next.js", "Nuxt.js",
    "FastAPI", "Django", "Flask", "Express.js", "NestJS", "Spring Boot",
    "Three.js", "Cesium", "Docker", "Kubernetes", "n8n", "Dify",
    "TypeScript", "Python", "Go", "Rust", "Java",
    "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
    "WebAssembly", "GraphQL", "gRPC", "Terraform", "CI/CD",
]


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT DEFAULT '',
                role TEXT DEFAULT 'user',
                receive_email INTEGER DEFAULT 1,
                tech_stack TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
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
                report_json TEXT,
                project_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                type TEXT DEFAULT 'suggestion',
                content TEXT NOT NULL,
                reply TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor = await db.execute("SELECT 1 FROM users WHERE username = 'admin'")
        if not await cursor.fetchone():
            await db.execute(
                "INSERT INTO users (username, password, role, tech_stack) VALUES (?, ?, ?, ?)",
                ("admin", hash_password("admin123"), "admin", json.dumps(DEFAULT_TECH_STACK, ensure_ascii=False))
            )
        cursor = await db.execute("SELECT 1 FROM config WHERE key = 'tech_stack'")
        if not await cursor.fetchone():
            await db.execute("INSERT INTO config (key, value) VALUES (?, ?)",
                ("tech_stack", json.dumps(DEFAULT_TECH_STACK, ensure_ascii=False)))
        cursor = await db.execute("SELECT 1 FROM config WHERE key = 'preset_types'")
        if not await cursor.fetchone():
            await db.execute("INSERT INTO config (key, value) VALUES (?, ?)",
                ("preset_types", json.dumps(PRESET_TECH_TYPES, ensure_ascii=False)))
        await db.commit()


# ---- Users ----
async def create_user(username: str, password: str, email: str = "", role: str = "user") -> dict:
    hashed = hash_password(password)
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO users (username, password, email, role, tech_stack) VALUES (?, ?, ?, ?, ?)",
                (username, hashed, email, role, json.dumps(DEFAULT_TECH_STACK, ensure_ascii=False))
            )
            await db.commit()
            cursor = await db.execute("SELECT id, username, email, role, receive_email, created_at FROM users WHERE username = ?", (username,))
            row = await cursor.fetchone()
            return {"id": row[0], "username": row[1], "email": row[2], "role": row[3], "receive_email": bool(row[4]), "created_at": row[5]}
        except aiosqlite.IntegrityError:
            return None

async def get_user_by_username(username: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_user_by_id(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, username, email, role, receive_email, tech_stack, created_at FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def list_users() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT id, username, email, role, receive_email, created_at FROM users ORDER BY id")
        return [dict(row) for row in await cursor.fetchall()]

async def update_user(user_id: int, **kwargs) -> bool:
    allowed = {"username", "email", "role", "password", "receive_email"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if "password" in fields:
        fields["password"] = hash_password(fields["password"])
    if not fields:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", (*fields.values(), user_id))
        await db.commit()
    return True

async def delete_user(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM users WHERE id = ? AND role != 'admin'", (user_id,))
        await db.commit()
        return cursor.rowcount > 0

async def get_all_user_emails() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT email FROM users WHERE email != '' AND receive_email = 1")
        rows = await cursor.fetchall()
        emails = []
        for row in rows:
            for e in row[0].split(","):
                e = e.strip()
                if e:
                    emails.append(e)
        return list(set(emails))


# ---- User Tech Stack ----
async def get_user_tech_stack(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT tech_stack FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return json.loads(row[0]) if row and row[0] else DEFAULT_TECH_STACK

async def set_user_tech_stack(user_id: int, stack: list[dict]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET tech_stack = ? WHERE id = ?", (json.dumps(stack, ensure_ascii=False), user_id))
        await db.commit()


# ---- Config ----
async def get_config(key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return json.loads(row[0]) if row else None

async def set_config(key: str, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, json.dumps(value, ensure_ascii=False)))
        await db.commit()

async def get_tech_stack() -> list[dict]:
    return await get_config("tech_stack") or DEFAULT_TECH_STACK

async def set_tech_stack(stack: list[dict]):
    await set_config("tech_stack", stack)

async def get_preset_types() -> list[str]:
    return await get_config("preset_types") or PRESET_TECH_TYPES

async def set_preset_types(types: list[str]):
    await set_config("preset_types", types)


# ---- Feedback ----
async def create_feedback(user_id: int, username: str, fb_type: str, content: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO feedback (user_id, username, type, content) VALUES (?, ?, ?, ?)",
            (user_id, username, fb_type, content)
        )
        await db.commit()
        fb_id = cursor.lastrowid
        cursor = await db.execute("SELECT * FROM feedback WHERE id = ?", (fb_id,))
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM feedback WHERE id = ?", (fb_id,))
        row = await cursor.fetchone()
        return dict(row) if row else {"id": fb_id}

async def list_feedback(user_id: int = None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if user_id:
            cursor = await db.execute("SELECT * FROM feedback WHERE user_id = ? ORDER BY id DESC", (user_id,))
        else:
            cursor = await db.execute("SELECT * FROM feedback ORDER BY id DESC")
        return [dict(row) for row in await cursor.fetchall()]

async def reply_feedback(fb_id: int, reply: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE feedback SET reply = ?, status = 'replied' WHERE id = ?", (reply, fb_id))
        await db.commit()
    return True


# ---- Dedup ----
async def is_recently_pushed(repo_name: str, dedup_days: int = 7) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cutoff = (date.today() - timedelta(days=dedup_days)).isoformat()
        cursor = await db.execute("SELECT 1 FROM pushed_repos WHERE repo_name = ? AND last_pushed >= ?", (repo_name, cutoff))
        return await cursor.fetchone() is not None

async def mark_pushed(repo_names: list[str]):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        for name in repo_names:
            await db.execute("""
                INSERT INTO pushed_repos (repo_name, first_seen, last_pushed, push_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(repo_name) DO UPDATE SET last_pushed = ?, push_count = push_count + 1
            """, (name, today, today, today))
        await db.commit()


# ---- Reports ----
async def save_report(report_html: str, report_json: str, project_count: int):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO daily_reports (report_date, report_html, report_json, project_count) VALUES (?, ?, ?, ?)",
            (today, report_html, report_json, project_count))
        await db.commit()

async def has_today_report() -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT 1 FROM daily_reports WHERE report_date = ?", (date.today().isoformat(),))
        return await cursor.fetchone() is not None

async def get_latest_report() -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM daily_reports ORDER BY report_date DESC LIMIT 1")
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_report_by_id(report_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM daily_reports WHERE id = ?", (report_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_report_history(limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, report_date, project_count, created_at FROM daily_reports ORDER BY report_date DESC LIMIT ?", (limit,))
        return [dict(row) for row in await cursor.fetchall()]
