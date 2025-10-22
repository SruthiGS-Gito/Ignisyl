"""
System Health Monitoring
Tracks real-time system resource usage
"""

import psutil
import platform
from datetime import datetime
from typing import Dict

class SystemMonitor:
    """Monitors system health and resource usage"""
    
    def __init__(self):
        self.start_time = datetime.now()
    
    def get_system_health(self) -> Dict:
        """
        Get current system health metrics
        
        Returns:
            Dictionary with CPU, memory, disk, network stats
        """
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024 ** 3)
        memory_total_gb = memory.total / (1024 ** 3)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        
        # Network throughput (bytes per second)
        net_io = psutil.net_io_counters()
        
        # System uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return {
            "cpu": {
                "usage_percent": round(cpu_percent, 1),
                "cores": cpu_count,
                "frequency_mhz": round(psutil.cpu_freq().current, 0) if psutil.cpu_freq() else 0
            },
            "memory": {
                "usage_percent": round(memory.percent, 1),
                "used_gb": round(memory_used_gb, 2),
                "total_gb": round(memory_total_gb, 2),
                "available_gb": round(memory.available / (1024 ** 3), 2)
            },
            "disk": {
                "usage_percent": round(disk.percent, 1),
                "used_gb": round(disk_used_gb, 2),
                "total_gb": round(disk_total_gb, 2),
                "free_gb": round(disk.free / (1024 ** 3), 2)
            },
            "network": {
                "bytes_sent_mb": round(net_io.bytes_sent / (1024 ** 2), 2),
                "bytes_recv_mb": round(net_io.bytes_recv / (1024 ** 2), 2),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "system": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "uptime_hours": round(uptime.total_seconds() / 3600, 1),
                "boot_time": boot_time.isoformat()
            }
        }
    
    def get_network_throughput(self) -> Dict:
        """Calculate current network throughput"""
        # Take first reading
        net_io_1 = psutil.net_io_counters()
        import time
        time.sleep(1)
        net_io_2 = psutil.net_io_counters()
        
        # Calculate throughput per second
        bytes_sent = (net_io_2.bytes_sent - net_io_1.bytes_sent) / (1024 ** 2)  # MB/s
        bytes_recv = (net_io_2.bytes_recv - net_io_1.bytes_recv) / (1024 ** 2)  # MB/s
        
        return {
            "upload_mbps": round(bytes_sent, 2),
            "download_mbps": round(bytes_recv, 2),
            "total_mbps": round(bytes_sent + bytes_recv, 2)
        }
    
    def get_process_count(self) -> Dict:
        """Get running process information"""
        processes = list(psutil.process_iter(['pid', 'name', 'status']))
        
        status_counts = {
            'running': 0,
            'sleeping': 0,
            'stopped': 0,
            'zombie': 0
        }
        
        for proc in processes:
            status = proc.info.get('status', 'unknown').lower()
            if 'running' in status:
                status_counts['running'] += 1
            elif 'sleeping' in status or 'idle' in status:
                status_counts['sleeping'] += 1
            elif 'stopped' in status:
                status_counts['stopped'] += 1
            elif 'zombie' in status:
                status_counts['zombie'] += 1
        
        return {
            "total_processes": len(processes),
            "status_breakdown": status_counts
        }

# Global instance
system_monitor = SystemMonitor()