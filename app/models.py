from dataclasses import dataclass, field, asdict


@dataclass
class TrendingRepo:
    name: str
    url: str
    description: str = ""
    language: str = ""
    stars: int = 0
    stars_today: int = 0
    forks: int = 0
    topics: list[str] = field(default_factory=list)
    readme_snippet: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalyzedRepo:
    repo: TrendingRepo
    category: str = "其他"
    summary_zh: str = ""
    detail_zh: str = ""
    tech_tags: list[str] = field(default_factory=list)
    relevance_score: float = 0.0
    relevance_reason: str = ""
    highlight: bool = False
    final_score: float = 0.0
