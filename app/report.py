from jinja2 import Template
from datetime import date
from app.models import AnalyzedRepo

EMAIL_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:700px;margin:0 auto;padding:20px;color:#333">
<h1 style="border-bottom:3px solid #f0883e;padding-bottom:10px">🔥 GitHub Trending 日报</h1>
<p style="color:#666">{{ report_date }} · 共 {{ total }} 个项目，推送 {{ pushed }} 个（{{ skipped }} 个近期已推）</p>
{% if highlights %}
<h2 style="color:#f0883e">🎯 与你技术栈相关</h2>
{% for item in highlights %}
<div style="border-left:4px solid #f0883e;padding:12px 16px;margin:12px 0;background:#fff8f0">
  <a href="{{ item.repo.url }}" style="font-size:18px;font-weight:bold;color:#0969da;text-decoration:none">{{ item.repo.name }}</a>
  <span style="background:#ddf4ff;color:#0969da;padding:2px 8px;border-radius:12px;font-size:12px;margin-left:8px">{{ item.category }}</span>
  <span style="color:#e3b341;margin-left:8px">⭐ {{ item.repo.stars }} (+{{ item.repo.stars_today }})</span>
  <p style="margin:8px 0 4px;font-size:15px">{{ item.summary_zh }}</p>
  <p style="margin:0;font-size:13px;color:#888">💡 {{ item.relevance_reason }} · 相关度 {{ item.relevance_score }}/10</p>
</div>
{% endfor %}
{% endif %}
<h2>📈 今日热门</h2>
<table style="width:100%;border-collapse:collapse">
<tr style="background:#f6f8fa"><th style="text-align:left;padding:8px">项目</th><th style="padding:8px">分类</th><th style="padding:8px">⭐ 今日</th><th style="text-align:left;padding:8px">摘要</th></tr>
{% for item in others %}
<tr style="border-bottom:1px solid #eee">
  <td style="padding:8px"><a href="{{ item.repo.url }}" style="color:#0969da;text-decoration:none">{{ item.repo.name.split('/')[1] }}</a></td>
  <td style="padding:8px;text-align:center;font-size:13px">{{ item.category }}</td>
  <td style="padding:8px;text-align:center;color:#e3b341">+{{ item.repo.stars_today }}</td>
  <td style="padding:8px;font-size:13px;color:#666">{{ item.summary_zh }}</td>
</tr>
{% endfor %}
</table>
<p style="margin-top:30px;padding-top:15px;border-top:1px solid #eee;color:#999;font-size:12px">
  Powered by <a href="https://github.com/rowan766/github-trending-agent" style="color:#999">GitHub Trending Agent</a>
</p>
</body></html>"""


def generate_report(analyzed: list[AnalyzedRepo], total_scraped: int, skipped_count: int) -> str:
    highlights = [a for a in analyzed if a.relevance_score >= 7]
    others = [a for a in analyzed if a.relevance_score < 7]
    return Template(EMAIL_TEMPLATE).render(
        report_date=date.today().strftime("%Y-%m-%d"),
        total=total_scraped, pushed=len(analyzed),
        skipped=skipped_count, highlights=highlights, others=others,
    )
