import json
import logging
from app.config import get_settings
from app.scraper import fetch_trending_multi
from app.github_api import enrich_repos
from app.analyzer import analyze_repos
from app.database import is_recently_pushed, mark_pushed, save_report, get_tech_stack
from app.report import generate_report
from app.emailer import send_report_email

logger = logging.getLogger(__name__)


class PipelineProgress:
    STEPS = [
        ("scraping", "\u6293\u53d6 Trending \u9875\u9762", 10),
        ("dedup", "\u53bb\u91cd\u8fc7\u6ee4", 20),
        ("enriching", "\u83b7\u53d6\u4ed3\u5e93\u8be6\u60c5", 45),
        ("analyzing", "AI \u5206\u6790\u8bc4\u5206", 70),
        ("report", "\u751f\u6210\u62a5\u544a", 88),
        ("email", "\u53d1\u9001\u90ae\u4ef6", 95),
        ("done", "\u5b8c\u6210", 100),
    ]

    def __init__(self):
        self.reset()

    def reset(self):
        self.percentage = 0
        self.step = "idle"
        self.message = "\u7b49\u5f85\u4e2d"

    def update(self, percentage: int, step: str, message: str):
        self.percentage = percentage
        self.step = step
        self.message = message

    def set_step(self, step_key: str, detail: str = ""):
        for key, label, pct in self.STEPS:
            if key == step_key:
                msg = f"{label}{'...' if pct < 100 else ''}"
                if detail:
                    msg += f" ({detail})"
                self.update(pct, key, msg)
                return

    def to_dict(self):
        return {"percentage": self.percentage, "step": self.step, "message": self.message}


pipeline_progress = PipelineProgress()


def _serialize_analyzed(analyzed_by_type: dict) -> str:
    result = {}
    for trending_type, analyzed_list in analyzed_by_type.items():
        items = []
        for a in analyzed_list:
            items.append({
                "name": a.repo.name, "url": a.repo.url,
                "description": a.repo.description, "language": a.repo.language,
                "stars": a.repo.stars, "stars_today": a.repo.stars_today,
                "forks": a.repo.forks, "topics": a.repo.topics,
                "readme_snippet": a.repo.readme_snippet,
                "category": a.category, "summary_zh": a.summary_zh,
                "relevance_score": a.relevance_score,
                "relevance_reason": a.relevance_reason,
                "highlight": a.highlight, "final_score": a.final_score,
                "trending_type": trending_type,
            })
        result[trending_type] = items
    return json.dumps(result, ensure_ascii=False)


async def run_pipeline() -> dict:
    settings = get_settings()
    languages = [l.strip() for l in settings.trending_languages.split(",")]

    pipeline_progress.set_step("scraping", "daily + weekly + monthly")
    logger.info("Step 1: Scraping (daily/weekly/monthly)...")
    multi = await fetch_trending_multi(languages)
    total_scraped = sum(len(v) for v in multi.values())
    if total_scraped == 0:
        pipeline_progress.update(100, "done", "\u65e0\u6570\u636e")
        return {"status": "no_data"}

    pipeline_progress.set_step("dedup", f"\u5171 {total_scraped} \u4e2a\u9879\u76ee")
    logger.info("Step 2: Dedup...")
    fresh_by_type = {}
    total_fresh = 0
    for t, repos in multi.items():
        fresh = [r for r in repos if not await is_recently_pushed(r.name, settings.dedup_days)]
        fresh_by_type[t] = fresh[:settings.max_projects]
        total_fresh += len(fresh_by_type[t])

    if total_fresh == 0:
        pipeline_progress.update(100, "done", "\u5168\u90e8\u5df2\u63a8\u9001")
        return {"status": "all_deduped"}

    all_unique = {}
    for t, repos in fresh_by_type.items():
        for r in repos:
            if r.name not in all_unique:
                all_unique[r.name] = r
    unique_list = list(all_unique.values())
    pipeline_progress.set_step("enriching", f"{len(unique_list)} \u4e2a\u9879\u76ee")
    logger.info(f"Step 3: Enriching {len(unique_list)} unique repos...")
    enriched_list = await enrich_repos(unique_list, settings.github_token)
    enriched_map = {r.name: r for r in enriched_list}
    for t in fresh_by_type:
        fresh_by_type[t] = [enriched_map[r.name] for r in fresh_by_type[t] if r.name in enriched_map]

    pipeline_progress.set_step("analyzing", f"{len(enriched_list)} \u4e2a\u9879\u76ee")
    logger.info("Step 4: Analyzing...")
    tech_stack = await get_tech_stack()
    analyzed_all = await analyze_repos(enriched_list, tech_stack)
    analyzed_map = {a.repo.name: a for a in analyzed_all}

    analyzed_by_type = {}
    total_pushed = 0
    for t in fresh_by_type:
        analyzed_by_type[t] = [analyzed_map[r.name] for r in fresh_by_type[t] if r.name in analyzed_map]
        total_pushed += len(analyzed_by_type[t])

    pipeline_progress.set_step("report")
    logger.info("Step 5: Report...")
    html = generate_report(analyzed_by_type, total_scraped, total_scraped - total_fresh)
    report_json = _serialize_analyzed(analyzed_by_type)
    await save_report(html, report_json, total_pushed)
    all_pushed_names = list({a.repo.name for al in analyzed_by_type.values() for a in al})
    await mark_pushed(all_pushed_names)

    pipeline_progress.set_step("email")
    logger.info("Step 6: Email...")
    email_sent = False
    try:
        email_sent = await send_report_email(html)
    except Exception as e:
        logger.error(f"Email failed: {e}")

    pipeline_progress.set_step("done", f"\u63a8\u9001 {total_pushed} \u4e2a\u9879\u76ee")
    return {"status": "success", "total": total_scraped, "pushed": total_pushed, "email": email_sent}
