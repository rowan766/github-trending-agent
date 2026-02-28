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
            for attempt in range(3):
                try:
                    resp = await client.get(url)
                    if resp.status_code == 429:
                        wait = 10 * (attempt + 1)
                        logger.warning(f"Rate limited on {url}, waiting {wait}s (attempt {attempt + 1}/3)")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    for repo in _parse_trending_page(resp.text):
                        if repo.name not in all_repos:
                            all_repos[repo.name] = repo
                    break
                except Exception as e:
                    if attempt < 2:
                        logger.warning(f"Failed to fetch {url} (attempt {attempt + 1}/3): {e}")
                        await asyncio.sleep(random.uniform(3, 5))
                    else:
                        logger.warning(f"Failed to fetch {url} after 3 attempts: {e}")
            await asyncio.sleep(random.uniform(1, 2))
    logger.info(f"Scraped {len(all_repos)} unique repos (since={since})")
    return list(all_repos.values())


async def fetch_by_topics(topics: list[str]) -> list[TrendingRepo]:
    all_repos: dict[str, TrendingRepo] = {}
    async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
        for topic in topics:
            url = f"https://api.github.com/search/repositories?q=topic:{topic}&sort=stars&order=desc&per_page=10"
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                for item in resp.json().get("items", []):
                    name = item["full_name"]
                    if name not in all_repos:
                        all_repos[name] = TrendingRepo(
                            name=name,
                            url=item["html_url"],
                            description=item.get("description") or "",
                            language=item.get("language") or "",
                            stars=item["stargazers_count"],
                            stars_today=0,
                            forks=item["forks_count"],
                        )
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Topic search failed for {topic}: {e}")
    return list(all_repos.values())


async def fetch_trending_multi(languages: list[str]) -> dict[str, list[TrendingRepo]]:
    """抓取 daily/weekly/monthly 三个维度"""
    result = {}
    for since in ["daily", "weekly", "monthly"]:
        result[since] = await fetch_trending(languages, since)
        logger.info(f"  {since}: {len(result[since])} repos")
        # 时间段之间额外等待，避免 GitHub 限流导致 weekly/monthly 拿不到数据
        await asyncio.sleep(random.uniform(3, 5))
    return result
