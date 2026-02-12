from jinja2 import Template
from datetime import date
from app.models import AnalyzedRepo

EMAIL_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:700px;margin:0 auto;padding:20px;color:#333">
<h1 style="border-bottom:3px solid #f0883e;padding-bottom:10px">🔥 GitHub Trending 日报</h1>
<p style="color:#666">{{ report_date }} · 共抛光 {{ total }} 个项目，推送 {{ pushed }} 个</p>

{% macro render_section(title, items, period) %}
{% if items %}
<h2 style="color:#f0883e;margin-top:30px;border-bottom:1px solid #eee;padding-bottom:8px">{{ title }}</h2>
{% set highlights = [] %}
{% set others = [] %}
{% for item in items %}
  {% if item.relevance_score >= 7 %}{% set _ = highlights.append(item) %}
  {% else %}{% set _ = others.append(item) %}{% endif %}
{% endfor %}
{% if highlights %}
<p style="font-size:14px;color:#888;margin:8px 0 4px">🎯 与你技术栈相关</p>
{% for item in highlights %}
<div style="border-left:4px solid #f0883e;padding:12px 16px;margin:10px 0;background:#fff8f0">
  <a href="{{ item.repo.url }}" style="font-size:16px;font-weight:bold;color:#0969da;text-decoration:none">{{ item.repo.name }}</a>
  <span style="background:#ddf4ff;color:#0969da;padding:2px 8px;border-radius:12px;font-size:12px;margin-left:8px">{{ item.category }}</span>
  <span style="color:#e3b341;margin-left:8px">⭐ {{ item.repo.stars }}{% if item.repo.stars_today %} (+{{ item.repo.stars_today }}){% endif %}</span>
  {% if item.repo.language %}<span style="color:#999;margin-left:8px;font-size:12px">{{ item.repo.language }}</span>{% endif %}
  <p style="margin:8px 0 4px;font-size:14px">{{ item.summary_zh }}</p>
  <p style="margin:0;font-size:12px;color:#888">💡 {{ item.relevance_reason }} · 相关度 {{ item.relevance_score }}/10</p>
</div>
{% endfor %}
{% endif %}
{% if others %}
<table style="width:100%;border-collapse:collapse;margin-top:8px">
<tr style="background:#f6f8fa"><th style="text-align:left;padding:6px 8px;font-size:13px">项目</th><th style="padding:6px 8px;font-size:13px">分类</th><th style="padding:6px 8px;font-size:13px">⭐ {{ period }}</th><th style="text-align:left;padding:6px 8px;font-size:13px">摘要</th></tr>
{% for item in others %}
<tr style="border-bottom:1px solid #eee">
  <td style="padding:6px 8px"><a href="{{ item.repo.url }}" style="color:#0969da;text-decoration:none;font-size:13px">{{ item.repo.name.split('/')[1] }}</a></td>
  <td style="padding:6px 8px;text-align:center;font-size:12px">{{ item.category }}</td>
  <td style="padding:6px 8px;text-align:center;color:#e3b341;font-size:13px">+{{ item.repo.stars_today }}</td>
  <td style="padding:6px 8px;font-size:12px;color:#666">{{ item.summary_zh[:60] }}{% if item.summary_zh|length > 60 %}...{% endif %}</td>
</tr>
{% endfor %}
</table>
{% endif %}
{% endif %}
{% endmacro %}

{{ render_section("⚡ 今日最热", daily, "今日") }}
{{ render_section("📈 本周飙升", weekly, "本周") }}
{{ render_section("📅 本月飙升", monthly, "本月") }}

<p style="margin-top:30px;padding-top:15px;border-top:1px solid #eee;color:#999;font-size:12px">
  Powered by <a href="https://github.com/rowan766/github-trending-agent" style="color:#999">GitHub Trending Agent</a>
</p>
</body></html>"""


def generate_report(analyzed_by_type: dict, total_scraped: int, skipped_count: int) -> str:
    """\u751f\u6210\u5305\u542b\u6240\u6709\u7ef4\u5ea6\u7684\u90ae\u4ef6\u62a5\u544a"""
    return Template(EMAIL_TEMPLATE).render(
        report_date=date.today().strftime("%Y-%m-%d"),
        total=total_scraped,
        pushed=sum(len(v) for v in analyzed_by_type.values()),
        daily=analyzed_by_type.get("daily", []),
        weekly=analyzed_by_type.get("weekly", []),
        monthly=analyzed_by_type.get("monthly", []),
    )
