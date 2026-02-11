import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseModel
from app.config import get_settings
from app.database import (
    init_db, get_latest_report, get_report_history,
    get_report_by_id, get_tech_stack, set_tech_stack
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


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/status")
async def status():
    return pipeline_status


@app.post("/api/trigger")
async def trigger(bg: BackgroundTasks):
    if pipeline_status["running"]:
        return {"status": "already_running"}
    bg.add_task(scheduled_job)
    return {"status": "triggered"}


class TechStackItem(BaseModel):
    name: str
    weight: int = 5
    enabled: bool = True
    preset: bool = False


@app.get("/api/config/tech-stack")
async def get_stack():
    return await get_tech_stack()


@app.put("/api/config/tech-stack")
async def update_stack(items: list[TechStackItem]):
    await set_tech_stack([item.model_dump() for item in items])
    return {"status": "ok"}


@app.get("/api/reports")
async def reports(limit: int = 50):
    return await get_report_history(limit)


@app.get("/api/reports/{report_id}")
async def report_detail(report_id: int):
    report = await get_report_by_id(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
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
