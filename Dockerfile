FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制需求文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY *.py ./
COPY urls.txt ./

# 创建非root用户
RUN useradd -m -u 1000 downloader
USER downloader

# 设置默认环境变量
ENV MAX_MEMORY_MB=100
ENV CHUNK_SIZE=8192
ENV DOWNLOAD_INTERVAL=2
ENV MAX_WORKERS=3

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://httpbin.org/status/200', timeout=5)" || exit 1

CMD ["python", "download_sync.py"]