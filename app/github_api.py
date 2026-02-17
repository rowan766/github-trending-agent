import httpx
import logging
from app.models import TrendingRepo

logger = logging.getLogger(__name__)
API_BASE = "https://api.github.com"


async def enrich_repo(repo: TrendingRepo, token: str = "") -> TrendingRepo:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(headers=headers, timeout=15) as client:
        try:
            resp = await client.get(f"{API_BASE}/repos/{repo.name}")
            if resp.status_code == 200:
                data = resp.json()
                repo.topics = data.get("topics", [])
                if not repo.description:
                    repo.description = data.get("description", "") or ""

            resp = await client.get(
                f"{API_BASE}/repos/{repo.name}/readme",
                headers={**headers, "Accept": "application/vnd.github.raw"}
            )
            if resp.status_code == 200:
                repo.readme_snippet = resp.text[:2000]
        except Exception as e:
            logger.warning(f"Failed to enrich {repo.name}: {e}")
    return repo


async def enrich_repos(repos: list[TrendingRepo], token: str = "") -> list[TrendingRepo]:
    return [await enrich_repo(r, token) for r in repos]
