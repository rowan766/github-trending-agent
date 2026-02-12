# GitHub Trending Agent 🔥

每日自动抓取 GitHub Trending 热门项目，AI 分析后通过邮件推送日报。

## 特性

- 🕷️ 自动抓取 GitHub Trending（多语言）
- 🤖 AI 分析分类 + 中文摘要（通义千问）
- 🎯 基于个人技术栈的个性化加权排序
- 📧 HTML 格式邮件日报推送
- 🔄 7 天去重，避免重复推送
- ⏰ APScheduler 定时任务，每天自动执行
- 🐳 Docker Compose 一键部署

## 快速开始

```bash
git clone https://github.com/rowan766/github-trending-agent.git
cd github-trending-agent
cp .env.example .env  # 编辑填入配置
docker compose up -d
```

## API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/trigger` | POST | 手动触发抓取+推送 |
| `/latest` | GET | 查看最近一次报告 |
| `/history` | GET | 历史报告列表 |

## 配置

参考 `.env.example`，主要配置项：

- `LLM_API_KEY` — 通义千问 API Key
- `SMTP_*` — 邮件 SMTP 配置
- `EMAIL_TO` — 收件邮箱
- `USER_TECH_STACK` — 你的技术栈（用于个性化排序）

## 启动项目

    - 删除旧数据库（表结构有变化）
        del data\trending.db

    - 安装新依赖
        .venv\Scripts\activate
        pip install python-jose[cryptography] passlib[bcrypt] --break-system-packages

    - 启动后端
        uvicorn app.main:app --reload --port 8000

     - 启动前端（另一个终端）
        cd web
        npm install
        npm run dev

## License

MIT
