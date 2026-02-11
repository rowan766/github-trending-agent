import httpx
from bs4 import BeautifulSoup
import asyncio
import random
import logging
from app.models import TrendingRepo

logger = logging.getLogger(__name__)
BASE_URL = "https://github.com/trending"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}


def _parse_int(text: str) -> int:
    return int(text.strip().replace(",", "")) if text and text.strip() else 0


def _parse_trending_page(html: str) -> list[TrendingRepo]:
    soup = BeautifulSoup(html, "html.parser")
    repos = []
    for article in soup.select("article.Box-row"):
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        name = h2.get("href", "").strip("/")
        if not name:
            continue

        desc_tag = article.select_one("p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        lang_tag = article.select_one("[itemprop='programmingLanguage']")
        language = lang_tag.get_text(strip=True) if lang_tag else ""

        links = article.select("a.Link--muted")
        stars = _parse_int(links[0].get_text()) if len(links) > 0 else 0
        forks = _parse_int(links[1].get_text()) if len(links) > 1 else 0

        today_tag = article.select_one("span.d-inline-block.float-sm-right")
        stars_today = 0
        if today_tag:
            text = today_tag.get_text(strip=True)
            stars_today = _parse_int(text.split()[0]) if text else 0

        repos.append(TrendingRepo(
            name=name, url=f"https://github.com/{name}",
            description=description, language=language,
            stars=stars, stars_today=stars_today, forks=forks,
        ))
    return repos


async def fetch_trending(languages: list[str], since: str = "daily") -> list[TrendingRepo]:
    all_repos: dict[str, TrendingRepo] = {}
    urls = [f"{BASE_URL}?since={since}"]
    urls += [f"{BASE_URL}/{lang}?since={since}" for lang in languages]

    async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        for url in urls:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                for repo in _parse_trending_page(resp.text):
                    if repo.name not in all_repos:
                        all_repos[repo.name] = repo
                await asyncio.sleep(random.uniform(1, 2))
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
    logger.info(f"Scraped {len(all_repos)} unique repos")
    return list(all_repos.values())
