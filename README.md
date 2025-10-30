# TrafficFlow - 流量去哪儿

TrafficFlow - 流量去哪儿 (刷下行流量小工具，基于python，Docker部署，仅消耗流量，不写入硬盘)

## 功能特性

- 🚀 无磁盘存储的文件下载
- 🎯 精确的速度限制（全局和单文件）
- 💾 内存优化，实时内存监控
- 🔄 可重复的下载循环
- 📊 实时统计信息和监控
- 🐳 Docker优化，资源限制
- ⚡ 同步和异步两种版本

## 版本区别

- **同步版本** (`download_sync.py`): 使用线程池，适合CPU密集型任务
- **异步版本** (`download_async.py`): 使用异步IO，适合高并发IO密集型任务

## 快速开始

### 1. 创建项目目录
```bash
mkdir traffic-flow
cd traffic-flow