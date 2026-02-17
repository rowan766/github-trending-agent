import asyncpg
import json
from datetime import date, timedelta
from app.auth import hash_password

TECH_DIRECTIONS = [
    {
        "name": "AI/LLM",
        "enabled": True,
        "tags": [
            "ai", "llm", "gpt", "openai", "langchain", "openclaw","transformer",
            "machine-learning", "deep-learning", "nlp", "chatgpt",
            "diffusion", "stable-diffusion", "pytorch", "tensorflow",
            "huggingface", "rag", "agent", "dify", "n8n", "comfyui",
            "ollama", "anthropic", "gemini", "claude", "mcp",
            "copilot", "cursor", "ai-coding", "tts", "whisper",
        ],
    },
    {
        "name": "前端",
        "enabled": True,
        "tags": [
            "vue", "vue.js", "react", "angular", "svelte", "next.js",
            "nextjs", "nuxt", "nuxt.js", "javascript", "typescript",
            "css", "html", "webpack", "vite", "tailwind", "element-plus",
            "ant-design", "frontend", "sass", "less", "pinia", "redux",
            "electron", "tauri", "pwa", "responsive", "uniapp", "taro",
        ],
    },
    {
        "name": "Web3",
        "enabled": False,
        "tags": [
            "web3", "blockchain", "ethereum", "solidity", "smart-contract",
            "defi", "nft", "dapp", "metamask", "hardhat", "foundry",
            "solana", "ipfs", "wallet", "crypto", "ton", "cosmos",
            "zk", "zero-knowledge", "layer2", "rollup",
        ],
    },
    {
        "name": "Java",
        "enabled": False,
        "tags": [
            "java", "spring", "spring-boot", "springboot", "maven",
            "gradle", "mybatis", "hibernate", "springcloud", "kafka",
            "tomcat", "netty", "jvm", "quarkus", "micronaut",
        ],
    },
    {
        "name": "Python",
        "enabled": False,
        "tags": [
            "python", "fastapi", "django", "flask", "pandas", "numpy",
            "scipy", "pip", "poetry", "scrapy", "celery", "asyncio",
            "pydantic", "sqlalchemy", "uvicorn",
        ],
    },
    {
        "name": "Go",
        "enabled": False,
        "tags": [
            "go", "golang", "gin", "echo", "beego", "fiber",
            "grpc", "protobuf", "cobra", "gorm",
        ],
    },
    {
        "name": "Rust",
        "enabled": False,
        "tags": [
            "rust", "cargo", "tokio", "wasm", "webassembly",
            "actix", "axum", "serde",
        ],
    },
    {
        "name": "测试/QA",
        "enabled": False,
        "tags": [
            "test", "testing", "jest", "pytest", "selenium", "cypress",
            "playwright", "unittest", "mocha", "qa", "e2e", "vitest",
            "coverage", "junit", "testng", "jmeter", "k6", "locust",
            "postman", "newman", "api-testing",
        ],
    },
    {
        "name": "运维/DevOps",
        "enabled": False,
        "tags": [
            "docker", "kubernetes", "k8s", "devops", "ci/cd", "jenkins",
            "terraform", "ansible", "nginx", "linux", "monitoring",
            "prometheus", "grafana", "helm", "github-actions", "gitlab-ci",
            "argocd", "istio", "envoy", "vault", "consul",
        ],
    },
    {
        "name": "UI/设计",
        "enabled": False,
        "tags": [
            "figma", "sketch", "design", "ui", "ux", "design-system",
            "icon", "animation", "lottie", "motion", "color", "font",
            "prototype", "wireframe", "storybook", "chromatic",
        ],
    },
    {
        "name": "产品/需求",
        "enabled": False,
        "tags": [
            "product", "requirement", "project-management", "agile",
            "scrum", "kanban", "roadmap", "analytics", "dashboard",
            "low-code", "no-code", "workflow", "automation", "saas",
            "crm", "erp", "bi", "data-visualization",
        ],
    },
    {
        "name": "3D可视化",
        "enabled": False,
        "tags": [
            "three.js", "threejs", "cesium", "webgl", "3d", "opengl",
            "unity", "unreal", "blender", "visualization", "gis",
            "mapbox", "deck.gl", "webgpu",
        ],
    },
    {
        "name": "移动端",
        "enabled": False,
        "tags": [
            "ios", "android", "swift", "kotlin", "flutter", "dart",
            "react-native", "expo", "swiftui", "jetpack-compose",
            "capacitor", "ionic", "mobile",
        ],
    },
    {
        "name": "数据库/存储",
        "enabled": False,
        "tags": [
            "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
            "sqlite", "neo4j", "clickhouse", "minio", "s3",
            "database", "sql", "nosql", "orm", "migration",
        ],
    },
]

# 兼容旧代码引用
DEFAULT_TECH_STACK = TECH_DIRECTIONS

# ---- Connection Pool ----
_pool: asyncpg.Pool | None = None


async def _init_connection(conn):
    """Register JSONB codec for automatic serialization."""
    await conn.set_type_codec(
        'jsonb',
        encoder=lambda v: json.dumps(v, ensure_ascii=False),
        decoder=json.loads,
        schema='pg_catalog',
    )


async def init_pool(database_url: str):
    global _pool
    _pool = await asyncpg.create_pool(
        database_url,
        min_size=2,
        max_size=10,
        command_timeout=30,
        init=_init_connection,
    )


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    assert _pool is not None, "Database pool not initialized"
    return _pool


# ---- Init (seed data only, DDL handled by init.sql) ----
async def init_db():
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT 1 FROM users WHERE username = 'admin'")
        if not row:
            await conn.execute(
                "INSERT INTO users (username, password, role, tech_stack) VALUES ($1, $2, $3, $4)",
                "admin", hash_password("admin123"), "admin",
                DEFAULT_TECH_STACK,
            )
        row = await conn.fetchrow("SELECT 1 FROM config WHERE key = 'tech_stack'")
        if not row:
            await conn.execute(
                "INSERT INTO config (key, value) VALUES ($1, $2)",
                "tech_stack", TECH_DIRECTIONS,
            )


# ---- Users ----
async def create_user(username: str, password: str, email: str = "", role: str = "user") -> dict:
    hashed = hash_password(password)
    async with get_pool().acquire() as conn:
        try:
            row = await conn.fetchrow(
                """INSERT INTO users (username, password, email, role, tech_stack)
                   VALUES ($1, $2, $3, $4, $5)
                   RETURNING id, username, email, role, receive_email, created_at""",
                username, hashed, email, role,
                DEFAULT_TECH_STACK,
            )
            return {
                "id": row["id"], "username": row["username"], "email": row["email"],
                "role": row["role"], "receive_email": bool(row["receive_email"]),
                "created_at": str(row["created_at"]),
            }
        except asyncpg.UniqueViolationError:
            return None


async def get_user_by_username(username: str) -> dict | None:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
        return dict(row) if row else None


async def get_user_by_id(user_id: int) -> dict | None:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, email, role, receive_email, tech_stack, created_at FROM users WHERE id = $1",
            user_id,
        )
        return dict(row) if row else None


async def list_users() -> list[dict]:
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, username, email, role, receive_email, created_at FROM users ORDER BY id"
        )
        return [dict(row) for row in rows]


async def update_user(user_id: int, **kwargs) -> bool:
    allowed = {"username", "email", "role", "password", "receive_email"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if "password" in fields:
        fields["password"] = hash_password(fields["password"])
    if not fields:
        return False
    keys = list(fields.keys())
    set_clause = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(keys))
    values = [fields[k] for k in keys]
    values.append(user_id)
    async with get_pool().acquire() as conn:
        await conn.execute(
            f"UPDATE users SET {set_clause} WHERE id = ${len(keys)+1}",
            *values,
        )
    return True


async def delete_user(user_id: int) -> bool:
    async with get_pool().acquire() as conn:
        result = await conn.execute(
            "DELETE FROM users WHERE id = $1 AND role != 'admin'", user_id
        )
        return result == "DELETE 1"


async def get_all_user_emails() -> list[str]:
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            "SELECT email FROM users WHERE email != '' AND receive_email = 1"
        )
        emails = []
        for row in rows:
            for e in row["email"].split(","):
                e = e.strip()
                if e:
                    emails.append(e)
        return list(set(emails))


async def get_users_for_email() -> list[dict]:
    """获取所有需要接收邮件的用户及其技术栈"""
    async with get_pool().acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, username, email, tech_stack FROM users WHERE email != '' AND receive_email = 1"
        )
        users = []
        for row in rows:
            emails = [e.strip() for e in row["email"].split(",") if e.strip()]
            if emails:
                tech_stack = row["tech_stack"] if row["tech_stack"] else TECH_DIRECTIONS
                users.append({
                    "id": row["id"],
                    "username": row["username"],
                    "emails": emails,
                    "tech_stack": tech_stack,
                })
        return users


# ---- User Tech Stack ----
async def get_user_tech_stack(user_id: int) -> list[dict]:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow("SELECT tech_stack FROM users WHERE id = $1", user_id)
        if row and row["tech_stack"]:
            return row["tech_stack"]
        return TECH_DIRECTIONS


async def set_user_tech_stack(user_id: int, stack: list[dict]):
    async with get_pool().acquire() as conn:
        await conn.execute(
            "UPDATE users SET tech_stack = $1 WHERE id = $2",
            stack, user_id,
        )


# ---- Config ----
async def get_config(key: str):
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow("SELECT value FROM config WHERE key = $1", key)
        return row["value"] if row else None


async def set_config(key: str, value):
    async with get_pool().acquire() as conn:
        await conn.execute(
            """INSERT INTO config (key, value) VALUES ($1, $2)
               ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
            key, value,
        )


async def get_tech_stack() -> list[dict]:
    return await get_config("tech_stack") or DEFAULT_TECH_STACK


async def set_tech_stack(stack: list[dict]):
    await set_config("tech_stack", stack)


async def get_preset_types() -> list[str]:
    """保留接口兼容，返回所有方向名称"""
    return [d["name"] for d in TECH_DIRECTIONS]


async def set_preset_types(types: list[str]):
    await set_config("preset_types", types)


# ---- Feedback ----
async def create_feedback(user_id: int, username: str, fb_type: str, content: str) -> dict:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO feedback (user_id, username, type, content)
               VALUES ($1, $2, $3, $4)
               RETURNING *""",
            user_id, username, fb_type, content,
        )
        return dict(row)


async def list_feedback(user_id: int = None) -> list[dict]:
    async with get_pool().acquire() as conn:
        if user_id:
            rows = await conn.fetch(
                "SELECT * FROM feedback WHERE user_id = $1 ORDER BY id DESC", user_id
            )
        else:
            rows = await conn.fetch("SELECT * FROM feedback ORDER BY id DESC")
        return [dict(row) for row in rows]


async def reply_feedback(fb_id: int, reply: str) -> bool:
    async with get_pool().acquire() as conn:
        await conn.execute(
            "UPDATE feedback SET reply = $1, status = 'replied' WHERE id = $2",
            reply, fb_id,
        )
    return True


# ---- Dedup ----
async def is_recently_pushed(repo_name: str, dedup_days: int = 7) -> bool:
    async with get_pool().acquire() as conn:
        cutoff = date.today() - timedelta(days=dedup_days)
        row = await conn.fetchrow(
            "SELECT 1 FROM pushed_repos WHERE repo_name = $1 AND last_pushed >= $2",
            repo_name, cutoff,
        )
        return row is not None


async def mark_pushed(repo_names: list[str]):
    today = date.today()
    async with get_pool().acquire() as conn:
        async with conn.transaction():
            for name in repo_names:
                await conn.execute(
                    """INSERT INTO pushed_repos (repo_name, first_seen, last_pushed, push_count)
                       VALUES ($1, $2, $3, 1)
                       ON CONFLICT (repo_name)
                       DO UPDATE SET last_pushed = $4, push_count = pushed_repos.push_count + 1""",
                    name, today, today, today,
                )


# ---- Reports ----
async def save_report(report_html: str, report_json, project_count: int):
    today = date.today()
    async with get_pool().acquire() as conn:
        await conn.execute(
            """INSERT INTO daily_reports (report_date, report_html, report_json, project_count)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (report_date)
               DO UPDATE SET report_html = EXCLUDED.report_html,
                             report_json = EXCLUDED.report_json,
                             project_count = EXCLUDED.project_count""",
            today, report_html, report_json, project_count,
        )


async def has_today_report() -> bool:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT 1 FROM daily_reports WHERE report_date = $1",
            date.today(),
        )
        return row is not None


async def has_today_email_sent() -> bool:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT 1 FROM daily_reports WHERE report_date = $1 AND email_sent = 1",
            date.today(),
        )
        return row is not None


async def get_latest_report() -> dict | None:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM daily_reports ORDER BY report_date DESC LIMIT 1"
        )
        return dict(row) if row else None


async def get_report_by_id(report_id: int) -> dict | None:
    async with get_pool().acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM daily_reports WHERE id = $1", report_id
        )
        return dict(row) if row else None


async def get_report_history(limit: int = 50, user_id: int = None) -> list[dict]:
    async with get_pool().acquire() as conn:
        if user_id:
            rows = await conn.fetch(
                """SELECT id, report_date, project_count, email_sent, created_at
                   FROM daily_reports
                   WHERE id NOT IN (SELECT report_id FROM user_hidden_reports WHERE user_id = $1)
                   ORDER BY report_date DESC LIMIT $2""",
                user_id, limit,
            )
        else:
            rows = await conn.fetch(
                """SELECT id, report_date, project_count, email_sent, created_at
                   FROM daily_reports ORDER BY report_date DESC LIMIT $1""",
                limit,
            )
        return [dict(row) for row in rows]


async def hide_report_for_user(user_id: int, report_id: int) -> bool:
    async with get_pool().acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO user_hidden_reports (user_id, report_id) VALUES ($1, $2)",
                user_id, report_id,
            )
            return True
        except asyncpg.UniqueViolationError:
            return True


async def mark_report_email_sent(report_date=None):
    today = report_date if isinstance(report_date, date) else date.today()
    async with get_pool().acquire() as conn:
        await conn.execute(
            "UPDATE daily_reports SET email_sent = 1 WHERE report_date = $1",
            today,
        )
