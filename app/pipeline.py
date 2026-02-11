import json
import logging
from app.config import get_settings
from app.scraper import fetch_trending
from app.github_api import enrich_repos
from app.analyzer import analyze_repos
from app.database import is_recently_pushed, mark_pushed, save_report, get_tech_stack
from app.report import generate_report
from app.emailer import send_report_email

logger = logging.getLogger(__name__)


def _serialize_analyzed(analyzed) -> str:
    items = []
    for a in analyzed:
        items.append({
            "name": a.repo.name, "url": a.repo.url,
            "description": a.repo.description, "language": a.repo.language,
            "stars": a.repo.stars, "stars_today": a.repo.stars_today,
            "forks": a.repo.forks, "topics": a.repo.topics,
            "category": a.category, "summary_zh": a.summary_zh,
            "relevance_score": a.relevance_score,
            "relevance_reason": a.relevance_reason,
            "highlight": a.highlight, "final_score": a.final_score,
        })
    return json.dumps(items, ensure_ascii=False)


async def run_pipeline() -> dict:
    settings = get_settings()
    languages = [l.strip() for l in settings.trending_languages.split(",")]

    logger.info("Step 1: Scraping...")
    repos = await fetch_trending(languages, settings.trending_since)
    total_scraped = len(repos)
    if not repos:
        return {"status": "no_data"}

    logger.info("Step 2: Dedup...")
    fresh = [r for r in repos if not await is_recently_pushed(r.name, settings.dedup_days)]
    skipped = total_scraped - len(fresh)
    if not fresh:
        return {"status": "all_deduped"}

    logger.info("Step 3: Enriching...")
    fresh = await enrich_repos(fresh[:settings.max_projects], settings.github_token)

    logger.info("Step 4: Analyzing...")
    tech_stack = await get_tech_stack()
    analyzed = await analyze_repos(fresh, tech_stack)

    logger.info("Step 5: Report...")
    html = generate_report(analyzed, total_scraped, skipped)
    report_json = _serialize_analyzed(analyzed)
    await save_report(html, report_json, len(analyzed))
    await mark_pushed([a.repo.name for a in analyzed])

    logger.info("Step 6: Email...")
    email_sent = False
    try:
        email_sent = await send_report_email(html)
    except Exception as e:
        logger.error(f"Email failed: {e}")

    return {"status": "success", "total": total_scraped, "skipped": skipped, "pushed": len(analyzed), "email": email_sent}
