import json
import logging
import random
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseModel
from typing import Optional
from app.config import get_settings

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
from app.auth import get_current_user, require_admin, verify_password, create_token
from app.database import (
    init_db, init_pool, close_pool,
    get_latest_report, get_report_history, get_report_by_id,
    get_tech_stack, set_tech_stack, get_user_tech_stack, set_user_tech_stack,
    create_user, get_user_by_username, get_user_by_id, list_users, update_user, delete_user,
    get_preset_types, set_preset_types, has_today_report, has_today_email_sent,
    create_feedback, list_feedback, reply_feedback,
    hide_report_for_user,
)
from app.cache import (
    init_redis, close_redis,
    get_pipeline_status, set_pipeline_status,
    get_pipeline_progress,
    get_user_trigger_count, increment_user_trigger,
    set_email_code, get_email_code, delete_email_code,
    set_email_verified, get_email_verified, clear_email_verified,
)
from app.pipeline import run_pipeline, pipeline_progress
from datetime import date
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def scheduled_job():
    await set_pipeline_status(True)
    await pipeline_progress.reset()
    try:
        result = await run_pipeline()
        await set_pipeline_status(False, result)
        logger.info(f"Result: {result}")
    except Exception as e:
        await set_pipeline_status(False, {"status": "error", "message": str(e)})
        await pipeline_progress.update(100, "error", f"失败: {e}")
        logger.error(f"Job failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Initialize database pool and Redis
    await init_pool(settings.database_url)
    await init_redis(settings.redis_url)
    await init_db()
    scheduler.add_job(scheduled_job, "cron", hour=settings.cron_hour, minute=settings.cron_minute, id="daily")
    scheduler.start()
    logger.info(f"Scheduler: daily {settings.cron_hour:02d}:{settings.cron_minute:02d} CST")
    yield
    scheduler.shutdown()
    await close_pool()
    await close_redis()


app = FastAPI(title="GitHub Trending Agent", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


# ---- Auth ----
class LoginReq(BaseModel):
    username: str
    password: str

class RegisterReq(BaseModel):
    username: str
    password: str
    email: str = ""

class ProfileUpdateReq(BaseModel):
    email: Optional[str] = None
    receive_email: Optional[bool] = None
    password: Optional[str] = None

class SendEmailCodeReq(BaseModel):
    email: str

class VerifyEmailCodeReq(BaseModel):
    email: str
    code: str


@app.post("/api/auth/login")
async def login(req: LoginReq):
    user = await get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(401, "Wrong username or password")
    token = create_token(user["id"], user["username"], user["role"])
    return {"token": token, "user": {
        "id": user["id"], "username": user["username"], "role": user["role"],
        "email": user.get("email", ""), "receive_email": bool(user.get("receive_email", 1)),
    }}

@app.post("/api/auth/register")
async def register(req: RegisterReq):
    if len(req.username) < 2 or len(req.password) < 6:
        raise HTTPException(400, "Username min 2 chars, password min 6 chars")
    user = await create_user(req.username, req.password, req.email)
    if not user:
        raise HTTPException(400, "Username already exists")
    token = create_token(user["id"], user["username"], user["role"])
    return {"token": token, "user": user}

@app.get("/api/auth/me")
async def me(user: dict = Depends(get_current_user)):
    info = await get_user_by_id(int(user["sub"]))
    if not info:
        raise HTTPException(404)
    info.pop("tech_stack", None)
    return info

@app.post("/api/auth/send-email-code")
async def send_email_code(req: SendEmailCodeReq, user: dict = Depends(get_current_user)):
    """向指定邮箱发送验证码，用于绑定邮箱前的验证"""
    from app.emailer import send_verification_code
    email = req.email.strip()
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "邮箱格式不正确")
    code = str(random.randint(100000, 999999))
    await set_email_code(email, code)
    sent = await send_verification_code(email, code)
    if not sent:
        raise HTTPException(500, "验证码发送失败，请检查服务器 SMTP 配置")
    return {"status": "ok", "message": "验证码已发送，请查收邮件"}


@app.post("/api/auth/verify-email-code")
async def verify_email_code_endpoint(req: VerifyEmailCodeReq, user: dict = Depends(get_current_user)):
    """验证邮箱验证码，验证通过后标记该邮箱为已验证状态（5分钟内有效）"""
    email = req.email.strip()
    stored = await get_email_code(email)
    if not stored or stored != req.code.strip():
        raise HTTPException(400, "验证码错误或已过期，请重新发送")
    await delete_email_code(email)
    await set_email_verified(int(user["sub"]), email)
    return {"status": "ok", "message": "邮箱验证成功"}


@app.put("/api/auth/profile")
async def update_profile(req: ProfileUpdateReq, user: dict = Depends(get_current_user)):
    user_id = int(user["sub"])
    fields = {}

    if req.email is not None:
        current_user_info = await get_user_by_id(user_id)
        current_email = current_user_info.get("email", "") or ""
        current_addrs = {e.strip() for e in current_email.split(",") if e.strip()}

        new_email_str = req.email.strip()
        new_addrs = [e.strip() for e in new_email_str.split(",") if e.strip()]

        if new_addrs:
            # Validate format for all new emails
            for addr in new_addrs:
                if not EMAIL_RE.match(addr):
                    raise HTTPException(400, f"邮箱格式不正确：{addr}")

            # Require verification for each newly added email address
            for addr in new_addrs:
                if addr not in current_addrs:
                    verified = await get_email_verified(user_id, addr)
                    if not verified:
                        raise HTTPException(400, f"邮箱 {addr} 尚未验证，请先发送验证码并验证后再保存")
                    await clear_email_verified(user_id, addr)

        fields["email"] = new_email_str

    if req.receive_email is not None:
        fields["receive_email"] = 1 if req.receive_email else 0
    if req.password is not None:
        if len(req.password) < 6:
            raise HTTPException(400, "Password min 6 chars")
        fields["password"] = req.password
    if not fields:
        raise HTTPException(400, "No fields to update")
    await update_user(user_id, **fields)
    info = await get_user_by_id(user_id)
    info.pop("tech_stack", None)
    return info


# ---- User Management (admin) ----
class UserUpdateReq(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

class AdminCreateUserReq(BaseModel):
    username: str
    password: str
    email: str = ""
    role: str = "user"

@app.get("/api/admin/users")
async def admin_list_users(_: dict = Depends(require_admin)):
    return await list_users()

@app.post("/api/admin/users")
async def admin_create_user(req: AdminCreateUserReq, _: dict = Depends(require_admin)):
    user = await create_user(req.username, req.password, req.email, req.role)
    if not user:
        raise HTTPException(400, "Username already exists")
    return user

@app.put("/api/admin/users/{user_id}")
async def admin_update_user(user_id: int, req: UserUpdateReq, _: dict = Depends(require_admin)):
    ok = await update_user(user_id, **req.model_dump(exclude_none=True))
    if not ok:
        raise HTTPException(400, "Update failed")
    return {"status": "ok"}

@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: int, _: dict = Depends(require_admin)):
    ok = await delete_user(user_id)
    if not ok:
        raise HTTPException(400, "Cannot delete admin or user not found")
    return {"status": "ok"}


# ---- Preset Types (admin) ----
@app.get("/api/admin/preset-types")
async def get_types(_: dict = Depends(require_admin)):
    return await get_preset_types()

@app.put("/api/admin/preset-types")
async def update_types(request: Request, _: dict = Depends(require_admin)):
    types = await request.json()
    await set_preset_types(types)
    return {"status": "ok"}


# ---- Feedback ----
class FeedbackReq(BaseModel):
    type: str = "suggestion"
    content: str

class ReplyReq(BaseModel):
    reply: str

@app.post("/api/feedback")
async def submit_feedback(req: FeedbackReq, user: dict = Depends(get_current_user)):
    if not req.content.strip():
        raise HTTPException(400, "Content required")
    fb = await create_feedback(int(user["sub"]), user["username"], req.type, req.content.strip())
    return fb

@app.get("/api/feedback")
async def get_my_feedback(user: dict = Depends(get_current_user)):
    return await list_feedback(int(user["sub"]))

@app.get("/api/admin/feedback")
async def admin_get_feedback(_: dict = Depends(require_admin)):
    return await list_feedback()

@app.put("/api/admin/feedback/{fb_id}/reply")
async def admin_reply_feedback(fb_id: int, req: ReplyReq, _: dict = Depends(require_admin)):
    await reply_feedback(fb_id, req.reply)
    return {"status": "ok"}


# ---- Tech Stack (per user) ----
@app.get("/api/config/tech-stack")
async def get_stack(user: dict = Depends(get_current_user)):
    return await get_user_tech_stack(int(user["sub"]))

@app.put("/api/config/tech-stack")
async def update_stack(request: Request, user: dict = Depends(get_current_user)):
    items = await request.json()
    await set_user_tech_stack(int(user["sub"]), items)
    return {"status": "ok"}

@app.get("/api/config/preset-types")
async def get_available_types(user: dict = Depends(get_current_user)):
    return await get_preset_types()


# ---- Pipeline ----
@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.get("/api/status")
async def status(user: dict = Depends(get_current_user)):
    ps = await get_pipeline_status()
    progress = await get_pipeline_progress()
    today_pushed = await has_today_report()
    return {**ps, "progress": progress, "today_pushed": today_pushed}

@app.post("/api/trigger")
async def trigger(bg: BackgroundTasks, user: dict = Depends(get_current_user)):
    ps = await get_pipeline_status()
    if ps["running"]:
        return {"status": "already_running"}

    # 管理员不限制
    if user.get("role") != "admin":
        uid = int(user["sub"])
        today = date.today().isoformat()

        trigger_date, count = await get_user_trigger_count(uid)

        # 日期不同视为 0
        if trigger_date != today:
            count = 0

        email_sent = await has_today_email_sent()

        if email_sent and count >= 1:
            return {"status": "limit_reached", "message": "今日已有邮件推送，且已额外触发过一次，无法再次触发"}
        if not email_sent and count >= 1:
            return {"status": "limit_reached", "message": "今日已触发过，请等待任务完成"}

        await increment_user_trigger(uid, today)

    bg.add_task(scheduled_job)
    return {"status": "triggered"}


# ---- Reports ----
@app.get("/api/reports")
async def reports(limit: int = 50, user: dict = Depends(get_current_user)):
    return await get_report_history(limit, user_id=int(user["sub"]))

@app.get("/api/reports/{report_id}")
async def report_detail(report_id: int, user: dict = Depends(get_current_user)):
    report = await get_report_by_id(report_id)
    if not report:
        raise HTTPException(404)
    result = dict(report)
    # JSONB columns are auto-deserialized, no need for json.loads
    if result.get("report_json"):
        result["projects"] = result["report_json"]
    return result

@app.delete("/api/reports/{report_id}")
async def delete_report(report_id: int, user: dict = Depends(get_current_user)):
    await hide_report_for_user(int(user["sub"]), report_id)
    return {"status": "ok"}

@app.get("/api/reports/{report_id}/html", response_class=HTMLResponse)
async def report_html(report_id: int):
    report = await get_report_by_id(report_id)
    if not report:
        raise HTTPException(404)
    return HTMLResponse(report["report_html"])


# Legacy
@app.get("/")
async def root():
    return {"status": "ok", "web": "/web/"}

@app.get("/latest", response_class=HTMLResponse)
async def latest():
    report = await get_latest_report()
    if not report:
        return HTMLResponse("<h1>暂无报告</h1>", status_code=404)
    return HTMLResponse(report["report_html"])

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/web", StaticFiles(directory=static_dir, html=True), name="web")
