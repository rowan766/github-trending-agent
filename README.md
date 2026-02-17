# GitHub Trending Agent

每日自动抓取 GitHub Trending 热门项目，AI 分析后通过邮件推送日报。

## 特性

- 自动抓取 GitHub Trending（多语言、daily/weekly/monthly）
- AI 分析分类 + 中文摘要 + 技术标签（通义千问）
- 基于个人技术栈的个性化评分与推送（每位用户收到不同的报告）
- HTML 格式邮件日报推送（个性化高亮区）
- 7 天去重，避免重复推送
- APScheduler 定时任务，每天自动执行
- Docker Compose 一键部署

## 快速开始（本地开发）

```bash
git clone https://github.com/rowan766/github-trending-agent.git
cd github-trending-agent
cp .env.example .env  # 编辑填入配置

# 启动后端
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 启动前端（另一个终端）
cd web
pnpm install
pnpm run dev
```

> 删除 `data/trending.db` 后重启服务，会自动重建表结构并创建默认管理员账号（admin / admin123）。

---

## 阿里云服务器部署指南

### 前提条件

- 阿里云 ECS 服务器（推荐 2C4G 及以上）
- 操作系统：Ubuntu 20.04+ / CentOS 7+
- 已安装 Docker 和 Docker Compose
- 安全组已开放 8000 端口

### 步骤 1：安装 Docker（如未安装）

```bash
# Ubuntu
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker && sudo systemctl start docker
sudo apt install -y docker-compose-plugin

# 验证
docker --version
docker compose version
```

### 步骤 2：上传项目到服务器

```bash
# 方式一：从 GitHub 克隆
git clone https://github.com/rowan766/github-trending-agent.git
cd github-trending-agent

# 方式二：本地打包上传
# 本地执行:
tar czf trending-agent.tar.gz --exclude=node_modules --exclude=.venv --exclude=data --exclude=__pycache__ .
scp trending-agent.tar.gz root@<你的服务器IP>:/opt/

# 服务器执行:
mkdir -p /opt/github-trending-agent && cd /opt/github-trending-agent
tar xzf /opt/trending-agent.tar.gz
```

### 步骤 3：配置环境变量

```bash
cp .env.example .env
vim .env
```

必须修改的配置项：

```ini
# LLM 配置（通义千问 DashScope）
LLM_API_KEY=你的千问API密钥
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# 邮件 SMTP 配置
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=你的邮箱@qq.com
SMTP_PASSWORD=你的授权码
EMAIL_TO=收件人@example.com

# 定时任务（北京时间）
CRON_HOUR=9
CRON_MINUTE=0

# GitHub Token（可选但强烈建议，否则 API 限额很低）
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# 抓取配置
TRENDING_LANGUAGES=python,javascript,typescript,vue,go,rust
MAX_PROJECTS=25
DEDUP_DAYS=7
```

### 步骤 4：构建并启动

```bash
# 构建镜像并后台启动（首次构建约 3-5 分钟）
docker compose up -d --build

# 查看启动日志
docker compose logs -f

# 确认服务健康
curl http://localhost:8000/api/health
# 期望返回: {"status":"ok"}
```

### 步骤 5：访问服务

- Web 管理界面：`http://<服务器IP>:8000/web/`
- 默认管理员账号：`admin` / `admin123`
- **首次登录后请立即修改密码**

### 日常运维命令

```bash
# 查看运行状态
docker compose ps

# 查看实时日志
docker compose logs -f --tail 100

# 重启服务
docker compose restart

# 更新部署（拉取最新代码后）
git pull
docker compose up -d --build

# 停止服务
docker compose down

# 查看容器健康状态
docker inspect --format='{{.State.Health.Status}}' github-trending-agent
```

### 数据备份

SQLite 数据库存储在 `./data/trending.db`，建议定期备份：

```bash
# 手动备份
cp data/trending.db data/trending.db.bak.$(date +%Y%m%d)

# 自动备份（crontab -e 添加）
0 3 * * * cp /opt/github-trending-agent/data/trending.db /opt/github-trending-agent/data/trending.db.bak.$(date +\%Y\%m\%d)
```

### 可选：Nginx 反向代理 + HTTPS

```bash
sudo apt install -y nginx
```

Nginx 配置 `/etc/nginx/sites-available/trending`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/trending /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 免费 SSL 证书（Let's Encrypt）
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 国内镜像加速（构建慢时使用）

如果服务器在国内，构建时拉取 npm/pip 包可能很慢，可以修改 Dockerfile 添加镜像源：

```dockerfile
# 在 pnpm install 之前添加
RUN npm config set registry https://registry.npmmirror.com

# 在 pip install 命令中添加 -i 参数
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 阿里云安全组配置

登录阿里云控制台 > ECS > 安全组 > 入方向规则，添加：

| 协议 | 端口范围 | 授权对象 | 说明 |
|------|---------|---------|------|
| TCP | 8000 | 0.0.0.0/0 | Trending Agent 服务 |
| TCP | 80 | 0.0.0.0/0 | HTTP（如配 Nginx） |
| TCP | 443 | 0.0.0.0/0 | HTTPS（如配 SSL） |

### 常见问题

| 问题 | 解决方案 |
|------|---------|
| 构建时 pnpm install / pip install 很慢 | 参考上方"国内镜像加速"章节 |
| 容器启动后无法访问 | 检查阿里云安全组是否开放 8000 端口 |
| 邮件发送失败 | 确认 SMTP 授权码正确，QQ 邮箱需开启 SMTP 服务 |
| GitHub 抓取被限流 | 配置 `GITHUB_TOKEN` 提高 API 限额 |
| 数据库重置 | 删除 `data/trending.db` 后重启容器即可 |

---

## 个性化评分方案

采用"共享抓取 + 共享分析 + 个性化评分"架构，在节省 LLM token 的同时实现真正的个性化推送。

### 流水线流程

```
抓取 GitHub Trending（1次，daily/weekly/monthly）
  → 去重过滤（1次）
  → GitHub API 补充信息（1次）
  → LLM 分析（1次，返回分类、摘要、技术标签）
  → 保存通用报告（供 Web 端查看）
  → 遍历每个用户：
      → 本地计算个性化评分（毫秒级）
      → 生成个性化报告（高亮区因人而异）
      → 发送个性化邮件
```

### 设计思路

- **LLM 只调用 1 次**：不带用户技术栈，只返回项目的 `tech_tags`（技术标签列表），token 成本不随用户数增长
- **个性化在本地完成**：用项目的 `tech_tags` + `language` + `topics` 与每个用户的技术栈做模糊匹配，纯计算无 API 调用
- **每个用户看到不同的报告**：高亮区基于各自的技术栈偏好

## API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/auth/login` | POST | 登录 |
| `/api/auth/register` | POST | 注册 |
| `/api/trigger` | POST | 手动触发流水线 |
| `/api/reports` | GET | 报告列表 |
| `/api/config/tech-stack` | GET/PUT | 技术栈配置 |

## 配置

参考 `.env.example`，主要配置项：

- `LLM_API_KEY` — 通义千问 API Key
- `SMTP_*` — 邮件 SMTP 配置
- `EMAIL_TO` — 兜底收件邮箱（未注册用户的收件地址）
- `GITHUB_TOKEN` — GitHub Token（提高 API 限额）
- `CRON_HOUR` / `CRON_MINUTE` — 定时执行时间

## License

MIT
