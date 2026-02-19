import json
import logging
from copy import deepcopy
from openai import AsyncOpenAI
from app.models import TrendingRepo, AnalyzedRepo
from app.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是 GitHub 项目分析助手。根据项目信息返回 JSON 数组。

对每个项目返回：
{{"name":"owner/repo","category":"AI/LLM|前端框架|DevOps/工具|编程语言/库|其他","summary_zh":"一句话中文摘要(50字内)","detail_zh":"详细中文介绍(200-300字)","tech_tags":["相关技术标签1","标签2","标签3"]}}

summary_zh 要求：一句话概括项目核心功能，50字以内。

detail_zh 要求（200-300字，用中文撰写）：
1. 项目概述：这个项目是什么，解决什么问题
2. 核心功能：列出3-5个主要功能亮点
3. 适用场景：哪些开发者/团队适合使用，典型使用场景
4. 快速上手：简要说明如何开始使用（如安装命令、基本用法）
请基于README和项目描述进行分析，信息不足的部分可以合理推断，但不要编造具体的API或命令。

tech_tags 要求：列出该项目涉及的技术关键词（3-8个），包括编程语言、框架、工具、领域等。
例如：["Python", "FastAPI", "AI/LLM", "REST API"] 或 ["TypeScript", "React", "Three.js", "WebGL", "3D"]
只返回 JSON。"""


def _build_project_text(repo: TrendingRepo) -> str:
    parts = [f"{repo.name} | {repo.language} | ⭐{repo.stars}(+{repo.stars_today}) | {repo.description}"]
    if repo.topics:
        parts.append(f"Topics: {','.join(repo.topics[:10])}")
    if repo.readme_snippet:
        parts.append(f"README: {repo.readme_snippet[:800]}")
    return "\n".join(parts)


async def analyze_repos(repos: list[TrendingRepo]) -> list[AnalyzedRepo]:
    """LLM 分析仓库，返回分类、摘要和技术标签（不含个性化评分）"""
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
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"分析以下{len(batch)}个项目:\n{projects_text}"}
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content
            if "```" in content:
                content = content.split("```json")[-1].split("```")[0] if "```json" in content else content.split("```")[1]
            parsed = json.loads(content.strip())
            items = parsed if isinstance(parsed, list) else parsed.get("projects", parsed.get("results", []))
            repo_map = {r.name: r for r in batch}
            for item in items:
                name = item.get("name", "")
                if name in repo_map:
                    repo = repo_map[name]
                    results.append(AnalyzedRepo(
                        repo=repo,
                        category=item.get("category", "其他"),
                        summary_zh=item.get("summary_zh", ""),
                        detail_zh=item.get("detail_zh", ""),
                        tech_tags=item.get("tech_tags", []),
                    ))
        except Exception as e:
            logger.error(f"AI analysis failed for batch {i}: {e}")
            for repo in batch:
                results.append(AnalyzedRepo(
                    repo=repo,
                    summary_zh=repo.description[:50],
                    tech_tags=[repo.language] if repo.language else [],
                ))
    return results


def compute_user_scores(analyzed_list: list[AnalyzedRepo], user_directions: list[dict]) -> list[AnalyzedRepo]:
    """根据用户选择的技术方向计算每个项目的个性化评分（无权重，纯标签匹配）"""
    # 收集用户所有启用方向的标签 → {tag: direction_name}
    user_tags = {}
    for direction in user_directions:
        if not direction.get("enabled", True):
            continue
        for tag in direction.get("tags", []):
            user_tags[tag.lower()] = direction["name"]

    results = []

    for a in analyzed_list:
        item = deepcopy(a)

        # 收集项目所有技术关键词（tech_tags + language + topics）
        project_tags = set()
        for tag in (item.tech_tags or []):
            project_tags.add(tag.lower())
        if item.repo.language:
            project_tags.add(item.repo.language.lower())
        for topic in (item.repo.topics or []):
            project_tags.add(topic.lower())

        # 匹配：项目标签与用户方向标签取交集
        matched_directions = set()
        matched_tags = []
        for tag in project_tags:
            if tag in user_tags:
                matched_directions.add(user_tags[tag])
                matched_tags.append(tag)
            else:
                # 模糊匹配（如 "vue.js" 匹配 "vue"）
                for user_tag, dir_name in user_tags.items():
                    if user_tag in tag or tag in user_tag:
                        matched_directions.add(dir_name)
                        matched_tags.append(tag)
                        break

        # 标记是否与用户方向相关
        item.highlight = len(matched_directions) > 0
        item.relevance_score = min(10, 4 + len(matched_directions) * 2) if matched_directions else 1
        item.relevance_reason = f"匹配: {', '.join(sorted(matched_directions)[:3])}" if matched_directions else ""
        item.final_score = item.repo.stars_today  # 排序按增星量
        results.append(item)

    results.sort(key=lambda x: x.repo.stars_today, reverse=True)
    return results
