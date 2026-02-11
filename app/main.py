import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import get_settings
from app.database import init_db, get_latest_report, get_report_history
from app.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def scheduled_job():
    logger.info("Scheduled job started")
    try:
        result = await run_pipeline()
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Job failed: {e}")


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


@app.get("/")
async def health():
    return {"status": "ok", "service": "github-trending-agent"}


@app.post("/trigger")
async def trigger(bg: BackgroundTasks):
    bg.add_task(run_pipeline)
    return {"status": "triggered"}


@app.get("/latest", response_class=HTMLResponse)
async def latest():
    report = await get_latest_report()
    if not report:
        return HTMLResponse("<h1>暂无报告</h1>", status_code=404)
    return HTMLResponse(report["report_html"])


@app.get("/history")
async def history(limit: int = 30):
    return await get_report_history(limit)
