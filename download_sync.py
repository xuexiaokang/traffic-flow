import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import sys
import os
import signal
import math
import psutil
import gc

class TrafficFlowManager:
    def __init__(self, max_memory_mb=100, chunk_size=8192):
        self.running = True
        self.downloaded_bytes = 0
        self.start_time = time.time()
        self.max_memory_mb = max_memory_mb
        self.chunk_size = chunk_size
        self.active_downloads = 0
        self.max_active_downloads = 3
        
        # 根据内存限制调整并发数
        self.adjust_concurrency_based_on_memory()
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def adjust_concurrency_based_on_memory(self):
        """根据可用内存调整并发数"""
        try:
            available_memory = psutil.virtual_memory().available / (1024 * 1024)
            safe_concurrency = max(1, min(10, int(available_memory * 0.1 / 10)))
            self.max_active_downloads = min(self.max_active_downloads, safe_concurrency)
            print(f"可用内存: {available_memory:.1f} MB, 设置最大并发数: {self.max_active_downloads}")
        except Exception as e:
            print(f"内存检测失败，使用默认并发数: {e}")
    
    def signal_handler(self, signum, frame):
        print(f"\n接收到信号 {signum}，正在停止程序...")
        self.running = False
    
    def get_memory_usage(self):
        """获取当前内存使用量"""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except:
            return 0
    
    def is_memory_safe(self):
        """检查内存是否安全"""
        memory_usage = self.get_memory_usage()
        return memory_usage < self.max_memory_mb
    
    def wait_for_memory_safe(self, timeout=30):
        """等待内存使用降到安全水平"""
        start_time = time.time()
        while self.running and time.time() - start_time < timeout:
            if self.is_memory_safe():
                return True
            print(f"内存使用过高 ({self.get_memory_usage():.1f} MB)，等待释放...")
            time.sleep(1)
        return self.is_memory_safe()
    
    def load_urls_from_file(self, filename='urls.txt'):
        """从文件加载URL列表"""
        urls = []
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        urls.append(line)
            print(f"从 {filename} 加载了 {len(urls)} 个URL")
        else:
            urls = [
                "https://httpbin.org/bytes/102400",
                "https://httpbin.org/bytes/1048576",
                "https://httpbin.org/bytes/5242880",
            ]
            print(f"使用默认测试URL ({len(urls)} 个)")
        
        return urls

    def limit_download_speed(self, chunk, max_speed_kbps):
        """限制下载速度"""
        if max_speed_kbps <= 0:
            return
            
        chunk_size = len(chunk)
        expected_time = chunk_size / (max_speed_kbps * 1024 / 8)
        
        actual_time = time.time() - getattr(self, '_last_chunk_time', time.time())
        if actual_time < expected_time:
            sleep_time = expected_time - actual_time
            time.sleep(sleep_time)
        
        self._last_chunk_time = time.time()

    def download_and_discard(self, url, timeout=30, max_speed_kbps=0):
        """下载文件并直接丢弃内容"""
        if not self.running:
            return False
        
        if not self.is_memory_safe():
            print(f"⚠️ 内存使用过高，跳过下载: {url}")
            return False
        
        with threading.Lock():
            if self.active_downloads >= self.max_active_downloads:
                print(f"⚠️ 并发数已达上限({self.max_active_downloads})，等待下载槽位...")
                time.sleep(1)
                return self.download_and_discard(url, timeout, max_speed_kbps)
            
            self.active_downloads += 1
        
        try:
            chunk_size = min(self.chunk_size, 4096)
            
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            total_size = 0
            chunk_count = 0
            
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not self.running:
                    return False
                
                total_size += len(chunk)
                self.downloaded_bytes += len(chunk)
                chunk_count += 1
                
                if chunk_count % 100 == 0:
                    gc.collect()
                
                if max_speed_kbps > 0:
                    self.limit_download_speed(chunk, max_speed_kbps)
                
                del chunk
            
            gc.collect()
            
            speed_info = ""
            if max_speed_kbps > 0:
                speed_info = f" (限速: {max_speed_kbps} KB/s)"
                
            memory_info = f" [内存: {self.get_memory_usage():.1f} MB]"
            print(f"✓ 成功下载并丢弃: {url} (大小: {total_size} 字节, 分块: {chunk_count}){speed_info}{memory_info}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ 下载失败 {url}: {e}")
            return False
        finally:
            self.active_downloads -= 1
            if 'response' in locals():
                response.close()

    def print_statistics(self):
        """打印统计信息"""
        elapsed_time = time.time() - self.start_time
        total_mb = self.downloaded_bytes / (1024 * 1024)
        avg_speed = total_mb / elapsed_time if elapsed_time > 0 else 0
        memory_usage = self.get_memory_usage()
        
        print(f"\n📊 统计信息:")
        print(f"   运行时间: {elapsed_time:.1f} 秒")
        print(f"   总下载量: {total_mb:.2f} MB")
        print(f"   平均速度: {avg_speed:.2f} MB/s")
        print(f"   内存使用: {memory_usage:.1f} MB / {self.max_memory_mb} MB")
        print(f"   活跃下载: {self.active_downloads}/{self.max_active_downloads}")

    def batch_download(self, urls, interval=1, max_workers=5, repeat_count=None, 
                      max_speed_kbps=0, per_download_speed_kbps=0):
        """批量下载文件"""
        count = 0
        
        max_workers = min(max_workers, self.max_active_downloads)
        
        self.downloaded_bytes = 0
        self.start_time = time.time()
        
        while self.running and (repeat_count is None or count < repeat_count):
            count += 1
            print(f"\n--- 第 {count} 轮下载开始 ---")
            print(f"并发设置: {max_workers} 工作线程, {self.max_active_downloads} 最大并发下载")
            
            if max_speed_kbps > 0:
                print(f"全局限速: {max_speed_kbps} KB/s")
            if per_download_speed_kbps > 0:
                print(f"单文件限速: {per_download_speed_kbps} KB/s")
            
            if not self.is_memory_safe():
                print("⚠️ 内存使用过高，等待释放...")
                if not self.wait_for_memory_safe():
                    print("❌ 内存释放超时，跳过本轮下载")
                    continue
            
            individual_speed = 0
            if per_download_speed_kbps > 0:
                individual_speed = per_download_speed_kbps
            elif max_speed_kbps > 0 and max_workers > 0:
                individual_speed = max_speed_kbps / max_workers
            
            download_semaphore = threading.Semaphore(self.max_active_downloads)
            
            def download_with_semaphore(url):
                with download_semaphore:
                    return self.download_and_discard(url, max_speed_kbps=individual_speed)
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(download_with_semaphore, urls))
            
            success_count = sum(1 for r in results if r)
            print(f"本轮完成: {success_count}/{len(urls)} 个文件")
            
            self.print_statistics()
            
            if (self.running and 
                (repeat_count is None or count < repeat_count)):
                print(f"等待 {interval} 秒后开始下一轮...")
                
                gc.collect()
                
                for i in range(interval):
                    if not self.running:
                        break
                    if i % 5 == 0:
                        memory_usage = self.get_memory_usage()
                        if memory_usage > self.max_memory_mb * 0.8:
                            print(f"⚠️ 内存使用较高: {memory_usage:.1f} MB，提前垃圾回收")
                            gc.collect()
                    time.sleep(1)

def main():
    max_memory_mb = int(os.getenv('MAX_MEMORY_MB', '100'))
    chunk_size = int(os.getenv('CHUNK_SIZE', '8192'))
    
    manager = TrafficFlowManager(
        max_memory_mb=max_memory_mb,
        chunk_size=chunk_size
    )
    
    interval = int(os.getenv('DOWNLOAD_INTERVAL', '2'))
    max_workers = int(os.getenv('MAX_WORKERS', '3'))
    repeat_count = os.getenv('REPEAT_COUNT')
    repeat_count = int(repeat_count) if repeat_count else None
    max_speed_kbps = int(os.getenv('MAX_SPEED_KBPS', '0'))
    per_download_speed_kbps = int(os.getenv('PER_DOWNLOAD_SPEED_KBPS', '0'))
    
    urls = manager.load_urls_from_file('/app/urls.txt')
    
    print("=" * 60)
    print("🚀 TrafficFlow - 网络流量测试工具")
    print("=" * 60)
    print(f"监控 URL 数量: {len(urls)}")
    print(f"下载间隔: {interval} 秒")
    print(f"工作线程: {max_workers}")
    print(f"最大并发下载: {manager.max_active_downloads}")
    print(f"内存限制: {max_memory_mb} MB")
    print(f"块大小: {chunk_size} 字节")
    print(f"重复次数: {'无限' if repeat_count is None else repeat_count}")
    if max_speed_kbps > 0:
        print(f"全局限速: {max_speed_kbps} KB/s")
    if per_download_speed_kbps > 0:
        print(f"单文件限速: {per_download_speed_kbps} KB/s")
    print("=" * 60)
    print("按 Ctrl+C 停止程序")
    
    try:
        manager.batch_download(
            urls=urls,
            interval=interval,
            max_workers=max_workers,
            repeat_count=repeat_count,
            max_speed_kbps=max_speed_kbps,
            per_download_speed_kbps=per_download_speed_kbps
        )
    except Exception as e:
        print(f"程序异常: {e}")
    finally:
        print("\n" + "=" * 60)
        print("最终统计信息:")
        manager.print_statistics()
        print("TrafficFlow 已停止")

if __name__ == "__main__":
    main()