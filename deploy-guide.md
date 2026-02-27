# GitHub Trending Agent 部署更新指南

> 项目路径：`/opt/trending-agent`

---

## 一、更新前端代码

### 本地操作
```bash
# 1. 修改前端代码后构建
pnpm run build

# 2. 用 XFTP 将 dist/ 目录下的文件上传到服务器
# 上传目标路径：/opt/trending-agent/app/static/
# 注意：覆盖上传，不要删除其他文件
```

### 服务器操作
```bash
cd /opt/trending-agent

# 重新构建镜像并重启（前端文件通过 COPY app/ app/ 打包进容器）
docker compose build --no-cache
docker compose up -d

# 验证文件是否进入容器
docker exec github-trending-agent ls /app/static/
```

---

## 二、更新后端代码

### 本地操作
```bash
# 用 XFTP 将修改的 .py 文件上传到服务器
# 上传目标路径：/opt/trending-agent/app/
```

### 服务器操作
```bash
cd /opt/trending-agent

# 重新构建并重启
docker compose build --no-cache
docker compose up -d

# 查看启动日志确认正常
docker logs github-trending-agent --tail 30
```

---

## 三、同时更新前后端

```bash
# 本地：先 build 前端，再上传所有文件到服务器

# 服务器：
cd /opt/trending-agent
docker compose build --no-cache
docker compose up -d
```

---

## 四、常用运维命令

```bash
# 查看容器状态
docker ps

# 查看实时日志
docker logs github-trending-agent -f

# 查看最近50条日志
docker logs github-trending-agent --tail 50

# 重启容器（不重新构建）
docker compose restart trending-agent

# 停止所有服务
docker compose down

# 启动所有服务
docker compose up -d
```

---

## 五、注意事项

1. **`.dockerignore` 不能包含 `app/static/`**，否则前端文件不会打包进容器
2. 每次修改代码后必须 `docker compose build` 重新构建，否则容器里还是旧代码
3. `docker compose restart` 只是重启容器，不会更新代码，必须用 `build`
4. 更新后可访问 `http://ip:8000/api/health` 确认服务正常
