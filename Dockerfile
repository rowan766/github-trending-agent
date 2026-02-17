# ============ 阶段1: 构建前端 ============
FROM node:20-slim AS frontend
WORKDIR /web
COPY web/package.json web/pnpm-lock.yaml* ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile
COPY web/ .
RUN pnpm run build

# ============ 阶段2: 生产镜像 ============
FROM python:3.11-slim
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY app/ app/

# 复制前端构建产物到后端静态目录（vite outDir: ../app/static → /app/static）
COPY --from=frontend /app/static app/static/

# 持久化数据目录
RUN mkdir -p /app/data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
