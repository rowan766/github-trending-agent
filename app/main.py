import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseModel
from typing import Optional
from app.config import get_settings
from app.auth import get_current_user, require_admin, verify_password, create_token
from app.database import (
    init_db, get_latest_report, get_report_history, get_report_by_id,
    get_tech_stack, set_tech_stack, get_user_tech_stack, set_user_tech_stack,
    create_user, get_user_by_username, get_user_by_id, list_users, update_user, delete_user,
    get_preset_types, set_preset_types,
)
from app.pipeline import run_pipeline
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
pipeline_status = {"running": False, "last_result": None}


async def scheduled_job():
    global pipeline_status
    pipeline_status["running"] = True
    try:
        result = await run_pipeline()
        pipeline_status["last_result"] = result
        logger.info(f"Result: {result}")
    except Exception as e:
        pipeline_status["last_result"] = {"status": "error", "message": str(e)}
        logger.error(f"Job failed: {e}")
    finally:
        pipeline_status["running"] = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    settings = get_settings()
    scheduler.add_job(scheduled_job, "cron", hour=settings.cron_hour, minute=settings.cron_minute, id="daily")
    scheduler.start()
    logger.info(f"Scheduler: daily {settings.cron_hour:02d}:{settings.cron_minute:02d} CST")
    yield
    scheduler.shutdown()


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


@app.put("/api/auth/profile")
async def update_profile(req: ProfileUpdateReq, user: dict = Depends(get_current_user)):
    user_id = int(user["sub"])
    fields = {}
    if req.email is not None:
        fields["email"] = req.email
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
async def update_types(types: list[str], _: dict = Depends(require_admin)):
    await set_preset_types(types)
    return {"status": "ok"}


# ---- Tech Stack (per user) ----

@app.get("/api/config/tech-stack")
async def get_stack(user: dict = Depends(get_current_user)):
    return await get_user_tech_stack(int(user["sub"]))


@app.put("/api/config/tech-stack")
async def update_stack(items: list, user: dict = Depends(get_current_user)):
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
    return pipeline_status


@app.post("/api/trigger")
async def trigger(bg: BackgroundTasks, user: dict = Depends(get_current_user)):
    if pipeline_status["running"]:
        return {"status": "already_running"}
    bg.add_task(scheduled_job)
    return {"status": "triggered"}


# ---- Reports ----

@app.get("/api/reports")
async def reports(limit: int = 50, user: dict = Depends(get_current_user)):
    return await get_report_history(limit)


@app.get("/api/reports/{report_id}")
async def report_detail(report_id: int, user: dict = Depends(get_current_user)):
    report = await get_report_by_id(report_id)
    if not report:
        raise HTTPException(404)
    result = dict(report)
    if result.get("report_json"):
        result["projects"] = json.loads(result["report_json"])
    return result


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


@app.post("/trigger")
async def trigger_legacy(bg: BackgroundTasks):
    bg.add_task(scheduled_job)
    return {"status": "triggered"}


@app.get("/latest", response_class=HTMLResponse)
async def latest():
    report = await get_latest_report()
    if not report:
        return HTMLResponse("<h1>\u6682\u65e0\u62a5\u544a</h1>", status_code=404)
    return HTMLResponse(report["report_html"])


static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/web", StaticFiles(directory=static_dir, html=True), name="web")
