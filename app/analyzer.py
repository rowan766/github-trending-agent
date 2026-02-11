import json
import logging
from openai import AsyncOpenAI
from app.models import TrendingRepo, AnalyzedRepo
from app.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是 GitHub 项目分析助手。根据项目信息返回 JSON 数组。

用户技术栈：{tech_stack}

对每个项目返回：
{{"name":"owner/repo","category":"AI/LLM|前端框架|DevOps/工具|编程语言/库|其他","summary_zh":"中文摘要(50字内)","relevance_score":1-10,"relevance_reason":"关联说明(30字内)","highlight":true/false}}

评分标准: 9-10=直接相关 7-8=高度相关 4-6=间接相关 1-3=弱相关
只返回 JSON。"""


def _build_project_text(repo: TrendingRepo) -> str:
    parts = [f"{repo.name} | {repo.language} | ⭐{repo.stars}(+{repo.stars_today}) | {repo.description}"]
    if repo.topics:
        parts.append(f"Topics: {','.join(repo.topics[:10])}")
    if repo.readme_snippet:
        parts.append(f"README: {repo.readme_snippet[:300]}")
    return "\n".join(parts)


async def analyze_repos(repos: list[TrendingRepo]) -> list[AnalyzedRepo]:
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    results: list[AnalyzedRepo] = []
    batch_size = 6

    for i in range(0, len(repos), batch_size):
        batch = repos[i:i + batch_size]
        projects_text = "\n---\n".join(_build_project_text(r) for r in batch)

        try:
            response = await client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT.format(tech_stack=settings.user_tech_stack)},
                    {"role": "user", "content": f"分析以下{len(batch)}个项目:\n{projects_text}"}
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content
            # 提取 JSON
            if "```" in content:
                content = content.split("```json")[-1].split("```")[0] if "```json" in content else content.split("```")[1]
            parsed = json.loads(content.strip())
            items = parsed if isinstance(parsed, list) else parsed.get("projects", parsed.get("results", []))

            repo_map = {r.name: r for r in batch}
            max_stars = max((r.stars_today for r in repos), default=1) or 1

            for item in items:
                name = item.get("name", "")
                if name in repo_map:
                    repo = repo_map[name]
                    relevance = item.get("relevance_score", 5)
                    norm_stars = (repo.stars_today / max_stars) * 10
                    final_score = norm_stars * 0.4 + relevance * 0.6

                    results.append(AnalyzedRepo(
                        repo=repo, category=item.get("category", "其他"),
                        summary_zh=item.get("summary_zh", ""),
                        relevance_score=relevance,
                        relevance_reason=item.get("relevance_reason", ""),
                        highlight=item.get("highlight", False),
                        final_score=round(final_score, 2),
                    ))
        except Exception as e:
            logger.error(f"AI analysis failed for batch {i}: {e}")
            for repo in batch:
                results.append(AnalyzedRepo(
                    repo=repo, summary_zh=repo.description[:50],
                    final_score=repo.stars_today * 0.4,
                ))

    results.sort(key=lambda x: x.final_score, reverse=True)
    return results
