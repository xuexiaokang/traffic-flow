# TrafficFlow - 流量去哪儿

TrafficFlow - 流量去哪儿 (刷下行流量小工具，采用python代码，Docker快速部署，仅消耗流量，不写入硬盘)

## 功能特性

- 🚀 无磁盘存储的文件下载
- 🎯 精确的速度限制（全局和单文件）
- 💾 内存优化，实时内存监控
- 🔄 可重复的下载循环
- 📊 实时统计信息和监控
- 🐳 Docker优化，资源限制
- ⚡ 同步和异步两种版本

## 项目结构
traffic-flow/
├── Dockerfile
├── requirements.txt
├── urls.txt（URL列表）
├── download_sync.py (同步版本)
├── download_async.py (异步版本)
├── docker-compose.yml
└── README.md

## 版本区别

- **同步版本** (`download_sync.py`): 使用线程池，适合CPU密集型任务
- **异步版本** (`download_async.py`): 使用异步IO，适合高并发IO密集型任务

## 快速开始

### 1. 创建项目目录
```bash
mkdir traffic-flow
cd traffic-flow
```
### 2. 创建配置文件
将本仓库中的所有文件复制到目录中。
### 3. 配置URL列表
编辑 urls.txt，添加您需要测试的实际文件URL：
```bash
# 替换为实际测试URL
https://your-cdn.com/large-file-1.zip
https://your-cdn.com/large-file-2.tar.gz
https://your-cdn.com/video-file.mp4
```
### 4. 构建Docker镜像
```bash
docker build -t traffic-flow .
```
### 5. 运行基本测试
同步版本
```bash
# 基本同步测试
docker run -d \
  --name traffic-flow-sync \
  -v $(pwd)/urls.txt:/app/urls.txt:ro \
  traffic-flow

# 限速同步测试 (500 KB/s)
docker run -d \
  --name traffic-flow-sync-speed \
  -e MAX_SPEED_KBPS=500 \
  -e DOWNLOAD_INTERVAL=3 \
  -e MAX_WORKERS=4 \
  -v $(pwd)/urls.txt:/app/urls.txt:ro \
  traffic-flow
```
异步版本
```bash
# 基本异步测试
docker run -d \
  --name traffic-flow-async \
  -v $(pwd)/urls.txt:/app/urls.txt:ro \
  traffic-flow \
  python download_async.py

# 高并发异步测试
docker run -d \
  --name traffic-flow-async-high \
  -e DOWNLOAD_INTERVAL=1 \
  -e PER_DOWNLOAD_SPEED_KBPS=100 \
  -v $(pwd)/urls.txt:/app/urls.txt:ro \
  traffic-flow \
  python download_async.py
```
内存优化测试
```bash
docker run -d \
  --name traffic-flow-mem-optimized \
  -e MAX_MEMORY_MB=50 \
  -e CHUNK_SIZE=4096 \
  -e MAX_WORKERS=2 \
  --memory=100m \
  -v $(pwd)/urls.txt:/app/urls.txt:ro \
  traffic-flow
```
### 6. 监控运行状态
```bash
# 查看实时日志
docker logs -f traffic-flow-sync

# 查看容器资源使用
docker stats traffic-flow-sync

# 查看最近日志
docker logs --tail 100 traffic-flow-sync
```
### 步骤7：使用Docker Compose（可选）
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```
## 环境变量配置速查
|配置项	|环境变量	|示例值	|说明|
|-------|-------|-------|-------|
|下载间隔	|DOWNLOAD_INTERVAL	|5	|每轮下载间隔(秒)|
|工作线程	|MAX_WORKERS	|5	|并发线程数(仅同步)|
|重复次数	|REPEAT_COUNT	|100	|下载轮次，空值=无限|
|全局限速	|MAX_SPEED_KBPS	|1000	|全局速度限制(KB/s)|
|单文件限速	|PER_DOWNLOAD_SPEED_KBPS	|200	|单文件速度限制(KB/s)|
|内存限制	|MAX_MEMORY_MB	|100	|最大内存使用(MB)|
|块大小	|CHUNK_SIZE	|4096	|下载数据块大小(字节)|
### 常用命令
管理容器
```bash
# 停止容器
docker stop traffic-flow-sync

# 重启容器
docker restart traffic-flow-sync

# 删除容器
docker rm traffic-flow-sync

# 批量停止所有TrafficFlow容器
docker stop $(docker ps -q --filter "name=traffic-flow")

# 批量删除所有TrafficFlow容器
docker rm $(docker ps -aq --filter "name=traffic-flow")
```
监控和调试
```bash
# 实时查看所有容器资源使用
docker stats $(docker ps --filter "name=traffic-flow" --format "{{.Names}}")

# 查看错误日志
docker logs traffic-flow-sync 2>&1 | grep -i error

# 查看统计信息
docker logs traffic-flow-sync 2>&1 | grep "统计信息"
```