from jinja2 import Template
from datetime import date
from app.models import AnalyzedRepo

EMAIL_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body id="top" style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:700px;margin:0 auto;padding:20px;color:#333">
<h1 style="border-bottom:3px solid #f0883e;padding-bottom:10px">🔥 GitHub Trending 日报</h1>
<p style="color:#666">{{ report_date }} · 共分析 {{ total }} 个项目，推送 {{ pushed }} 个</p>

{% macro render_item(item, show_total_stars=false) %}
<div style="padding:12px 16px;margin:10px 0;background:#fafbfc;border:1px solid #eee;border-radius:8px{% if item.highlight %};border-left:4px solid #f0883e;background:#fff8f0{% endif %}">
  <div>
    <a href="{{ item.repo.url }}" style="font-size:16px;font-weight:bold;color:#0969da;text-decoration:none">{{ item.repo.name }}</a>
    <span style="background:#ddf4ff;color:#0969da;padding:2px 8px;border-radius:12px;font-size:12px;margin-left:8px">{{ item.category }}</span>
    {% if item.highlight %}<span style="background:#fff0e0;color:#f0883e;padding:2px 8px;border-radius:12px;font-size:12px;margin-left:4px">🎯 相关</span>{% endif %}
    {% if show_total_stars %}
    <span style="color:#e3b341;margin-left:8px">⭐ {{ item.repo.stars }}</span>
    {% else %}
    <span style="color:#e3b341;margin-left:8px">⭐ {{ item.repo.stars }}{% if item.repo.stars_today %} (+{{ item.repo.stars_today }}){% endif %}</span>
    {% endif %}
    {% if item.repo.language %}<span style="color:#999;margin-left:8px;font-size:12px">{{ item.repo.language }}</span>{% endif %}
  </div>
  <p style="margin:8px 0 4px;font-size:14px">{{ item.summary_zh|e }}</p>
  {% if item.relevance_reason %}<p style="margin:0;font-size:12px;color:#888">💡 {{ item.relevance_reason|e }}</p>{% endif %}
</div>
{% endmacro %}

{% macro render_section(title, items, show_total_stars=false) %}
{% if items %}
<h2 style="color:#f0883e;margin-top:30px;border-bottom:1px solid #eee;padding-bottom:8px">{{ title }}</h2>
{% for item in items %}
{{ render_item(item, show_total_stars) }}
{% endfor %}
{% endif %}
{% endmacro %}

{{ render_section("🔥 最热项目", hottest, true) }}
{{ render_section("⚡ 今日最热", daily) }}
{{ render_section("📈 本周飙升", weekly) }}
{{ render_section("📅 本月飙升", monthly) }}

<p style="margin-top:30px;padding-top:15px;border-top:1px solid #eee;color:#999;font-size:12px">
  Powered by <a href="https://github.com/rowan766/github-trending-agent" style="color:#999">GitHub Trending Agent</a>
</p>

<a href="#top" style="position:fixed;bottom:30px;right:30px;width:40px;height:40px;background:#f0883e;color:#fff;border-radius:50%;text-align:center;line-height:40px;font-size:20px;text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,0.2);z-index:999" title="回到顶部">↑</a>
</body></html>"""


def generate_report(analyzed_by_type: dict, total_scraped: int, skipped_count: int) -> str:
    """生成包含所有维度的邮件报告"""
    daily = analyzed_by_type.get("daily", [])
    weekly = analyzed_by_type.get("weekly", [])
    monthly = analyzed_by_type.get("monthly", [])

    # 合并所有项目，按 repo.name 去重，按总星数降序，取 Top 10
    seen = {}
    for item in daily + weekly + monthly:
        if item.repo.name not in seen:
            seen[item.repo.name] = item
    hottest = sorted(seen.values(), key=lambda x: x.repo.stars, reverse=True)[:10]

    # 各维度去掉已在"最热项目"中出现的，避免重复渲染导致邮件过大被截断
    hottest_names = {item.repo.name for item in hottest}
    daily = [item for item in daily if item.repo.name not in hottest_names]
    weekly = [item for item in weekly if item.repo.name not in hottest_names]
    monthly = [item for item in monthly if item.repo.name not in hottest_names]

    return Template(EMAIL_TEMPLATE).render(
        report_date=date.today().strftime("%Y-%m-%d"),
        total=total_scraped,
        pushed=sum(len(v) for v in analyzed_by_type.values()),
        hottest=hottest,
        daily=daily,
        weekly=weekly,
        monthly=monthly,
    )
