"""
Real-time Network Activity Monitor for IGNISYL
Monitors actual laptop network usage and sends data to the threat detection API
The monitor will:
1. Check your network every 30 seconds
2. Print current network usage
3. Detect if you transfer more than 100MB
4. Send suspicious activity to your API
5. Show the risk analysis results
"""

import psutil
import time
import requests
from datetime import datetime
from typing import Dict, List
import asyncio
import sys
import os
# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class NetworkMonitor:
    """
    Monitors network activity on your laptop in real-time
    Detects suspicious patterns and sends them to the API for analysis
    """
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        self.api_url = api_url
        self.baseline_bytes = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        self.last_check_time = time.time()
        self.alert_threshold_mb = 100  # Alert if more than 100MB transferred in 30 seconds
        self.monitoring_active = False
        
        # Load user configuration
        self.user_config = self._load_user_config()
        
        print("🔍 Network Monitor initialized")
        print(f"📡 Monitoring network activity on this laptop")
        print(f"👤 User: {self.user_config['full_name']} ({self.user_config['user_id']})")
        print(f"🎯 Alert threshold: {self.alert_threshold_mb}MB in 30 seconds")
    
    def _load_user_config(self) -> Dict:
        """Load user configuration from config file"""
        import json
        config_path = os.path.join(os.path.dirname(__file__), 'user_config.json')
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                print(f"✅ Loaded config for user: {config['full_name']}")
                return config
        except FileNotFoundError:
            print("⚠️ user_config.json not found. Using default 'local_user'")
            return {
                "user_id": "local_user",
                "username": "local_user",
                "full_name": "Local User",
                "department": "IT",
                "role": "Developer"
            }
        except Exception as e:
            print(f"⚠️ Error loading config: {e}. Using default.")
            return {
                "user_id": "local_user",
                "username": "local_user",
                "full_name": "Local User",
                "department": "IT",
                "role": "Developer"
            }
    
    def get_current_network_usage(self) -> Dict:
        """
        Gets current network statistics from your laptop
        
        Returns:
            Dict with bytes sent, received, and transfer rate
        """
        # psutil.net_io_counters() reads network interface statistics
        net_stats = psutil.net_io_counters()
        
        current_time = time.time()
        time_elapsed = current_time - self.last_check_time
        
        # Calculate how many bytes transferred since last check
        current_bytes = net_stats.bytes_sent + net_stats.bytes_recv
        bytes_transferred = current_bytes - self.baseline_bytes
        
        # Convert to megabytes
        mb_transferred = bytes_transferred / (1024 * 1024)
        
        # Calculate transfer rate (MB per second)
        transfer_rate_mbps = mb_transferred / time_elapsed if time_elapsed > 0 else 0
        
        return {
            "bytes_sent": net_stats.bytes_sent,
            "bytes_received": net_stats.bytes_recv,
            "bytes_transferred": bytes_transferred,
            "mb_transferred": round(mb_transferred, 2),
            "transfer_rate_mbps": round(transfer_rate_mbps, 2),
            "time_elapsed": round(time_elapsed, 1)
        }
    
    def get_active_connections(self) -> List[Dict]:
        """
        Gets list of active network connections on your laptop
        Shows which programs are using the network
        
        Returns:
            List of active connections with IP addresses and ports
        """
        connections = []
        
        try:
            # psutil.net_connections() gets all network connections
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED':  # Only active connections
                    connections.append({
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                        "status": conn.status,
                        "pid": conn.pid  # Process ID
                    })
        except Exception as e:
            print(f"⚠️ Error getting connections: {e}")
        
        return connections
    
    def detect_suspicious_activity(self, network_usage: Dict) -> bool:
        """
        Analyzes network usage to detect suspicious patterns
        
        Args:
            network_usage: Current network statistics
            
        Returns:
            True if suspicious, False if normal
        """
        mb_transferred = network_usage['mb_transferred']
        transfer_rate = network_usage['transfer_rate_mbps']
        
        # Suspicious if:
        # 1. Large transfer in short time (more than 100MB in 30 seconds)
        # 2. Very high transfer rate (more than 50 MB/s)
        
        if mb_transferred > self.alert_threshold_mb:
            print(f"🚨 ALERT: Large data transfer detected: {mb_transferred}MB")
            return True
        
        if transfer_rate > 50:
            print(f"⚠️ WARNING: High transfer rate: {transfer_rate} MB/s")
            return True
        
        return False
    
    def send_to_api(self, activity_data: Dict):
        """
        Sends detected activity to your threat detection API for analysis
        AND broadcasts to WebSocket for real-time dashboard updates
        
        Args:
            activity_data: Activity information to analyze
        """
        try:
            # Make HTTP POST request to your /analyze endpoint
            response = requests.post(
                f"{self.api_url}/api/v1/analyze",
                json=activity_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                risk_score = result['risk_assessment']['final_risk_score']
                risk_level = result['risk_assessment']['risk_level']
                action = result['firewall_action']['action']
                
                print(f"📊 API Response: Risk={risk_score} Level={risk_level} Action={action}")
                
                # If high risk, show alert
                if risk_level == "HIGH":
                    print(f"🚨 HIGH RISK DETECTED! Recommended action: {action}")
                
                # Broadcast threat alert via WebSocket using HTTP
                try:
                    threat_alert = {
                        "user_id": activity_data.get("user_id"),
                        "threat_type": "large_data_transfer",
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "action": action,
                        "bytes_transferred": activity_data.get("bytes_transferred"),
                        "timestamp": activity_data.get("timestamp"),
                        "summary": result['explanation']['summary']
                    }
                    
                    # Send HTTP request to broadcast endpoint
                    broadcast_response = requests.post(
                        f"{self.api_url}/api/v1/broadcast/threat",
                        json=threat_alert,
                        timeout=5
                    )
                    if broadcast_response.status_code == 200:
                        print("📡 WebSocket broadcast sent to all connected dashboards")
                    else:
                        print(f"⚠️ WebSocket broadcast failed: {broadcast_response.status_code}")
                        
                except Exception as ws_error:
                    print(f"⚠️ WebSocket broadcast failed: {ws_error}")
                
                return result
            else:
                print(f"❌ API request failed: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to API. Is the server running?")
        except Exception as e:
            print(f"❌ Error sending to API: {e}")
                
    def monitor_loop(self, check_interval: int = 30):
        """
        Main monitoring loop - runs continuously
        Checks network activity every X seconds
        
        Args:
            check_interval: How often to check (in seconds)
        """
        self.monitoring_active = True
        print(f"\n🟢 Network monitoring started (checking every {check_interval} seconds)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.monitoring_active:
                # Get current network usage
                network_usage = self.get_current_network_usage()
                
                print(f"📈 Network Activity: {network_usage['mb_transferred']}MB transferred "
                      f"({network_usage['transfer_rate_mbps']} MB/s)")
                
                # Check if suspicious
                if self.detect_suspicious_activity(network_usage):
                    # Get active connections for context
                    connections = self.get_active_connections()
                    
                    # Prepare activity data for API
                    activity_data = {
                        "user_id": "local_user",
                        "activity_type": "network_activity",
                        "timestamp": datetime.now().isoformat(),
                        "file_size": int(network_usage['bytes_transferred']),
                        "bytes_transferred": int(network_usage['bytes_transferred']),
                        "transfer_rate_mbps": network_usage['transfer_rate_mbps'],
                        "active_connections": len(connections),
                        "department": "IT",
                        "role": "Developer"
                    }
                    
                    # Send to API for analysis
                    print("📤 Sending suspicious activity to API...")
                    self.send_to_api(activity_data)
                
                # Update baseline for next check
                net_stats = psutil.net_io_counters()
                self.baseline_bytes = net_stats.bytes_sent + net_stats.bytes_recv
                self.last_check_time = time.time()
                
                # Wait before next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            self.monitoring_active = False
    
    def start_monitoring(self, interval: int = 30):
        """
        Start the network monitoring in the foreground
        
        Args:
            interval: Check interval in seconds
        """
        self.monitor_loop(interval)

# Standalone script mode
if __name__ == "__main__":
    print("=" * 60)
    print("IGNISYL - Real-time Network Monitor")
    print("=" * 60)
    print()
    
    # Create monitor instance
    monitor = NetworkMonitor()
    
    # Start monitoring (checks every 30 seconds)
    monitor.start_monitoring(interval=30)