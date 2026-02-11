import logging
from app.config import get_settings
from app.scraper import fetch_trending
from app.github_api import enrich_repos
from app.analyzer import analyze_repos
from app.database import is_recently_pushed, mark_pushed, save_report
from app.report import generate_report
from app.emailer import send_report_email

logger = logging.getLogger(__name__)


async def run_pipeline() -> dict:
    settings = get_settings()
    languages = [l.strip() for l in settings.trending_languages.split(",")]

    # 1. 抓取
    logger.info("Step 1: Scraping...")
    repos = await fetch_trending(languages, settings.trending_since)
    total_scraped = len(repos)
    if not repos:
        return {"status": "no_data"}

    # 2. 去重
    logger.info("Step 2: Dedup...")
    fresh = [r for r in repos if not await is_recently_pushed(r.name, settings.dedup_days)]
    skipped = total_scraped - len(fresh)
    if not fresh:
        return {"status": "all_deduped"}

    # 3. 补充元数据
    logger.info("Step 3: Enriching...")
    fresh = await enrich_repos(fresh[:settings.max_projects], settings.github_token)

    # 4. AI 分析
    logger.info("Step 4: Analyzing...")
    analyzed = await analyze_repos(fresh)

    # 5. 生成报告
    logger.info("Step 5: Report...")
    html = generate_report(analyzed, total_scraped, skipped)
    await save_report(html, len(analyzed))
    await mark_pushed([a.repo.name for a in analyzed])

    # 6. 发送邮件
    logger.info("Step 6: Email...")
    email_sent = False
    try:
        email_sent = await send_report_email(html)
    except Exception as e:
        logger.error(f"Email failed: {e}")

    return {"status": "success", "total": total_scraped, "skipped": skipped, "pushed": len(analyzed), "email": email_sent}
