# ========= 基础镜像 =========
FROM python:3.12-slim

# ========= 环境变量 =========
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ========= 工作目录 =========
WORKDIR /app

# ========= 换源（可选，加速） =========

# ========= 系统依赖 =========
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ========= 依赖安装（缓存关键） =========
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ========= 复制代码 =========
COPY . .

# ========= 安全：非 root =========
RUN useradd -m appuser
USER appuser

# ========= 端口 =========
EXPOSE 8000

# ========= 启动 =========
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]