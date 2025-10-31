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
