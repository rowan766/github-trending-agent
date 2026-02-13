# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

GitHub Trending Agent —— 全栈应用，每日自动抓取 GitHub 趋势仓库，通过阿里千问大模型进行分析摘要，根据用户个人技术栈偏好生成个性化排名，并以 HTML 邮件形式推送报告。

## 常用命令

### 后端

```bash
# 开发启动
uvicorn app.main:app --reload --port 8000

# 安装依赖
pip install -r requirements.txt

# Docker 部署
docker compose up -d
```

### 前端

```bash
cd web
pnpm install
pnpm run dev       # Vite 开发服务器 (默认 http://localhost:5173)
pnpm run build     # 生产构建
```

### 数据库重置

删除 `data/trending.db` 后重启服务，`init_db()` 会自动重建表结构并创建默认管理员账号（admin / admin123）。

## 架构概览

### 后端（`app/`）—— Python FastAPI + SQLite

| 文件 | 职责 |
|------|------|
| `main.py` | FastAPI 应用入口，注册所有 API 路由，挂载静态文件，启动 APScheduler 定时任务 |
| `pipeline.py` | 核心流水线编排：抓取 → 去重 → GitHub API 补充 → LLM 分析 → 生成报告 → 发送邮件 → 存库 |
| `scraper.py` | BeautifulSoup 解析 GitHub Trending 页面（支持多语言、多时间段） |
| `github_api.py` | 调用 GitHub API 获取 topics、README 等补充信息 |
| `analyzer.py` | 调用阿里千问（OpenAI 兼容接口），批量分析仓库（每批 6 个） |
| `report.py` | Jinja2 模板生成 HTML 邮件报告（高亮区 + 表格区） |
| `emailer.py` | SMTP 邮件发送 |
| `database.py` | SQLite 异步操作（aiosqlite），表结构初始化 |
| `auth.py` | JWT 认证（HS256，72 小时过期）+ bcrypt 密码哈希 |
| `config.py` | Pydantic Settings，从 `.env` 读取配置 |
| `models.py` | 数据模型定义（TrendingRepo、AnalyzedRepo） |

### 前端（`web/`）—— Vue 3 + Element Plus + Pinia

- **路由**（`router/index.js`）：Hash 模式，公开路由 `/login`，受保护路由需 localStorage token，管理员路由需 `role === 'admin'`
- **状态管理**（`stores/`）：`user.js`（认证）、`report.js`（报告列表与流水线状态）、`techStack.js`（技术栈偏好）
- **API 客户端**（`api/index.js`）：Axios 实例，拦截器自动注入 JWT token，401 时自动登出

### 数据流水线流程

1. `scraper` 抓取 GitHub Trending（daily/weekly/monthly 三个时间段）
2. 查 `pushed_repos` 表做 7 天去重
3. `github_api` 补充 topics、README
4. `analyzer` 批量调用千问 LLM（分类、中文摘要、相关性评分 1-10）
5. 计算最终得分：`final_score = norm_stars * 0.4 + relevance * 0.6`
6. 相关性 >= 7 的项目进入高亮区，其余进入表格区
7. `emailer` 通过 SMTP 发送给所有 `receive_email=1` 的用户
8. 报告 HTML + JSON 存入 `daily_reports` 表，仓库记录存入 `pushed_repos`

## 主要 API 路径

- `/api/auth/*` — 登录、注册、个人资料
- `/api/config/tech-stack` — 用户技术栈配置
- `/api/config/preset-types` — 预设技术类型
- `/api/reports` — 报告列表与详情
- `/api/trigger` — 手动触发流水线
- `/api/status` — 流水线运行状态与进度
- `/api/feedback` — 用户反馈
- `/api/admin/*` — 管理员接口（用户管理、反馈回复、预设类型）

## 关键配置（`.env`）

- `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` — 千问 LLM 连接
- `SMTP_*` — 邮件发送配置
- `CRON_HOUR` / `CRON_MINUTE` — 定时执行时间（北京时间）
- `TRENDING_LANGUAGES` — 抓取的编程语言列表
- `MAX_PROJECTS` — 每次最大处理项目数
- `DEDUP_DAYS` — 去重天数（默认 7）

## 数据库表（SQLite）

- `users` — 用户信息、技术栈（JSON）、邮件偏好
- `daily_reports` — 每日报告（HTML + JSON）
- `pushed_repos` — 已推送仓库去重记录
- `config` — 全局配置（预设类型等）
- `feedback` — 用户反馈与管理员回复

## 注意事项

- 前端构建产物放在 `web/src/static/`，后端通过 `StaticFiles` 挂载在 `/web` 路径
- JWT secret 当前硬编码在 `auth.py` 中，生产环境应修改
- LLM 使用 OpenAI SDK 兼容模式连接阿里云 DashScope
- 抓取 GitHub Trending 时有 1-2 秒随机延迟防止被封
