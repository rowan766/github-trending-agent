import json
import logging
from app.config import get_settings
from app.scraper import fetch_trending_multi
from app.github_api import enrich_repos
from app.analyzer import analyze_repos, compute_user_scores
from app.database import (
    is_recently_pushed, mark_pushed, save_report,
    get_users_for_email, DEFAULT_TECH_STACK,
)
from app.report import generate_report
from app.emailer import send_report_email, send_email_to_user

logger = logging.getLogger(__name__)


class PipelineProgress:
    STEPS = [
        ("scraping", "抓取 Trending 页面", 10),
        ("dedup", "去重过滤", 20),
        ("enriching", "获取仓库详情", 45),
        ("analyzing", "AI 分析评分", 70),
        ("report", "生成报告", 85),
        ("email", "发送个性化邮件", 92),
        ("done", "完成", 100),
    ]

    def __init__(self):
        self.reset()

    def reset(self):
        self.percentage = 0
        self.step = "idle"
        self.message = "等待中"

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
                "tech_tags": a.tech_tags,
                "relevance_score": a.relevance_score,
                "relevance_reason": a.relevance_reason,
                "highlight": a.highlight, "final_score": a.final_score,
                "trending_type": trending_type,
            })
        result[trending_type] = items
    return json.dumps(result, ensure_ascii=False)


def _score_by_type(analyzed_map: dict, fresh_by_type: dict, tech_stack: list[dict]) -> dict:
    """对每个时间维度的项目按指定技术栈计算个性化评分"""
    scored_by_type = {}
    for t in fresh_by_type:
        type_analyzed = [analyzed_map[r.name] for r in fresh_by_type[t] if r.name in analyzed_map]
        scored_by_type[t] = compute_user_scores(type_analyzed, tech_stack)
    return scored_by_type


async def run_pipeline() -> dict:
    settings = get_settings()
    languages = [l.strip() for l in settings.trending_languages.split(",")]

    # Step 1: 抓取
    pipeline_progress.set_step("scraping", "daily + weekly + monthly")
    logger.info("Step 1: Scraping (daily/weekly/monthly)...")
    multi = await fetch_trending_multi(languages)
    total_scraped = sum(len(v) for v in multi.values())
    if total_scraped == 0:
        pipeline_progress.update(100, "done", "无数据")
        return {"status": "no_data"}

    # Step 2: 去重
    pipeline_progress.set_step("dedup", f"共 {total_scraped} 个项目")
    logger.info("Step 2: Dedup...")
    fresh_by_type = {}
    total_fresh = 0
    for t, repos in multi.items():
        fresh = [r for r in repos if not await is_recently_pushed(r.name, settings.dedup_days)]
        fresh_by_type[t] = fresh[:settings.max_projects]
        total_fresh += len(fresh_by_type[t])

    if total_fresh == 0:
        pipeline_progress.update(100, "done", "全部已推送")
        return {"status": "all_deduped"}

    # Step 3: 补充信息（去重后只处理唯一项目）
    all_unique = {}
    for t, repos in fresh_by_type.items():
        for r in repos:
            if r.name not in all_unique:
                all_unique[r.name] = r
    unique_list = list(all_unique.values())
    pipeline_progress.set_step("enriching", f"{len(unique_list)} 个项目")
    logger.info(f"Step 3: Enriching {len(unique_list)} unique repos...")
    enriched_list = await enrich_repos(unique_list, settings.github_token)
    enriched_map = {r.name: r for r in enriched_list}
    for t in fresh_by_type:
        fresh_by_type[t] = [enriched_map[r.name] for r in fresh_by_type[t] if r.name in enriched_map]

    # Step 4: LLM 分析（只做一次，不含个性化评分）
    pipeline_progress.set_step("analyzing", f"{len(enriched_list)} 个项目")
    logger.info("Step 4: Analyzing (no personalization)...")
    analyzed_all = await analyze_repos(enriched_list)
    analyzed_map = {a.repo.name: a for a in analyzed_all}

    total_pushed = sum(
        len([r for r in fresh_by_type[t] if r.name in analyzed_map])
        for t in fresh_by_type
    )

    # Step 5: 生成通用报告（用默认技术栈评分，供 Web 端查看）
    pipeline_progress.set_step("report")
    logger.info("Step 5: Generating default report for web...")
    default_scored = _score_by_type(analyzed_map, fresh_by_type, DEFAULT_TECH_STACK)
    default_html = generate_report(default_scored, total_scraped, total_scraped - total_fresh)
    report_json = _serialize_analyzed(default_scored)
    await save_report(default_html, report_json, total_pushed)

    all_pushed_names = list({r.name for repos in fresh_by_type.values() for r in repos if r.name in analyzed_map})
    await mark_pushed(all_pushed_names)

    # Step 6: 为每个用户生成个性化报告并发送邮件
    pipeline_progress.set_step("email")
    logger.info("Step 6: Sending personalized emails...")
    email_sent = False
    users = await get_users_for_email()

    # 收集已由用户邮件覆盖的地址，避免兜底邮件重复发送
    user_email_set = set()
    for user in users:
        user_email_set.update(user["emails"])

    for user in users:
        try:
            user_scored = _score_by_type(analyzed_map, fresh_by_type, user["tech_stack"])
            user_html = generate_report(user_scored, total_scraped, total_scraped - total_fresh)
            sent = await send_email_to_user(user_html, user["emails"])
            if sent:
                email_sent = True
                logger.info(f"Personalized email sent to user {user['username']}")
        except Exception as e:
            logger.error(f"Failed to send email to user {user['username']}: {e}")

    # 兜底：向 .env 中配置但不在用户列表中的收件人发送默认报告
    try:
        env_emails = set()
        if settings.email_to:
            for e in settings.email_to.split(","):
                if e.strip():
                    env_emails.add(e.strip())
        extra_emails = env_emails - user_email_set
        if extra_emails:
            sent = await send_email_to_user(default_html, list(extra_emails))
            if sent:
                email_sent = True
                logger.info(f"Default report sent to env recipients: {extra_emails}")
    except Exception as e:
        logger.error(f"Failed to send default email: {e}")

    pipeline_progress.set_step("done", f"推送 {total_pushed} 个项目，{len(users)} 位用户")
    return {"status": "success", "total": total_scraped, "pushed": total_pushed, "email": email_sent, "users_notified": len(users)}
