"""
Real-time Network Activity Monitor for IGNISYL
Monitors actual laptop network usage and sends data to the threat detection API
"""

import psutil
import time
import requests
from datetime import datetime
from typing import Dict, List
import sys
import os
import json
import logging

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from config.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkMonitor:
    """
    Monitors network activity on your laptop in real-time
    Detects suspicious patterns and sends them to the API for analysis
    
    Features:
    - Real-time network usage tracking
    - Suspicious activity detection
    - Integration with threat detection API
    - WebSocket broadcasting for dashboard
    """
    
    def __init__(self, api_url: str = None):
        self.api_url = api_url or f"http://{settings.API_HOST}:{settings.API_PORT}"
        
        # Initialize network baseline
        net_stats = psutil.net_io_counters()
        self.baseline_bytes = net_stats.bytes_sent + net_stats.bytes_recv
        self.last_check_time = time.time()
        
        # Alert thresholds
        self.alert_threshold_mb = 100  # Alert if >100MB in check interval
        self.high_rate_threshold_mbps = 50  # Alert if >50 MB/s
        
        self.monitoring_active = False
        
        # Load user configuration
        self.user_config = self._load_user_config()
        
        logger.info("🔍 Network Monitor initialized")
        logger.info(f"📡 Monitoring network activity on this device")
        logger.info(f"👤 User: {self.user_config['full_name']} (ID: {self.user_config['user_id']})")
        logger.info(f"🎯 Alert threshold: {self.alert_threshold_mb}MB")
    
    def _load_user_config(self) -> Dict:
        """Load user configuration from config file"""
        config_path = os.path.join(settings.DATA_PATH, 'user_config.json')
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"✅ Loaded config for user: {config['full_name']}")
                    return config
            else:
                logger.warning(f"⚠️ Config file not found at {config_path}")
                return self._create_default_config(config_path)
                
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return self._create_default_config(config_path)
    
    def _create_default_config(self, config_path: str) -> Dict:
        """Create default user config file"""
        default_config = {
            "user_id": 1,  # Use first user from database
            "username": "admin",
            "full_name": "System Administrator",
            "department": "IT",
            "role": "Administrator"
        }
        
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"✅ Created default config at {config_path}")
            logger.info("💡 Edit this file to customize the monitored user")
            
        except Exception as e:
            logger.error(f"❌ Could not create config file: {e}")
        
        return default_config
    
    def get_current_network_usage(self) -> Dict:
        """
        Gets current network statistics from your device
        
        Returns:
            Dict with bytes sent, received, and transfer rate
        """
        try:
            net_stats = psutil.net_io_counters()
            
            current_time = time.time()
            time_elapsed = current_time - self.last_check_time
            
            # Calculate bytes transferred since last check
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
            
        except Exception as e:
            logger.error(f"❌ Error getting network usage: {e}")
            return {}
    
    def get_active_connections(self) -> List[Dict]:
        """
        Gets list of active network connections
        Shows which programs are using the network
        
        Returns:
            List of active connections with IP addresses and ports
        """
        connections = []
        
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED':
                    connections.append({
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                        "status": conn.status,
                        "pid": conn.pid
                    })
        except PermissionError:
            logger.warning("⚠️ Insufficient permissions to get all connections (run as admin)")
        except Exception as e:
            logger.error(f"❌ Error getting connections: {e}")
        
        return connections
    
    def detect_suspicious_activity(self, network_usage: Dict) -> bool:
        """
        Analyzes network usage to detect suspicious patterns
        
        Args:
            network_usage: Current network statistics
            
        Returns:
            True if suspicious, False if normal
        """
        if not network_usage:
            return False
        
        mb_transferred = network_usage.get('mb_transferred', 0)
        transfer_rate = network_usage.get('transfer_rate_mbps', 0)
        
        # Suspicious if:
        # 1. Large transfer in short time
        if mb_transferred > self.alert_threshold_mb:
            logger.warning(f"🚨 ALERT: Large data transfer: {mb_transferred}MB")
            return True
        
        # 2. Very high transfer rate
        if transfer_rate > self.high_rate_threshold_mbps:
            logger.warning(f"⚠️ WARNING: High transfer rate: {transfer_rate} MB/s")
            return True
        
        return False
    
    def send_to_api(self, activity_data: Dict) -> Dict:
        """
        Sends detected activity to threat detection API
        AND broadcasts to WebSocket for real-time dashboard updates
        
        Args:
            activity_data: Activity information to analyze
            
        Returns:
            API response or empty dict on error
        """
        try:
            # Send to /analyze endpoint
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
                
                logger.info(f"📊 API Response: Risk={risk_score} Level={risk_level} Action={action}")
                
                # Alert if high risk
                if risk_level in ["HIGH", "CRITICAL"]:
                    logger.warning(f"🚨 {risk_level} RISK DETECTED! Action: {action}")
                
                # Broadcast via WebSocket
                try:
                    threat_alert = {
                        "user_id": activity_data.get("user_id"),
                        "threat_type": "network_activity",
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "action": action,
                        "bytes_transferred": activity_data.get("bytes_transferred"),
                        "timestamp": activity_data.get("timestamp"),
                        "summary": result['explanation']['summary']
                    }
                    
                    broadcast_response = requests.post(
                        f"{self.api_url}/api/v1/broadcast/threat",
                        json=threat_alert,
                        timeout=5
                    )
                    
                    if broadcast_response.status_code == 200:
                        logger.info("📡 WebSocket broadcast sent to dashboards")
                    
                except Exception as ws_error:
                    logger.debug(f"WebSocket broadcast note: {ws_error}")
                
                return result
                
            else:
                logger.error(f"❌ API request failed: {response.status_code}")
                return {}
                
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Cannot connect to API at {self.api_url}. Is the server running?")
            return {}
        except Exception as e:
            logger.error(f"❌ Error sending to API: {e}")
            return {}
    
    def monitor_loop(self, check_interval: int = 30):
        """
        Main monitoring loop - runs continuously
        Checks network activity every X seconds
        
        Args:
            check_interval: How often to check (in seconds)
        """
        self.monitoring_active = True
        
        logger.info(f"\n🟢 Network monitoring started (checking every {check_interval}s)")
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            while self.monitoring_active:
                # Get current network usage
                network_usage = self.get_current_network_usage()
                
                if network_usage:
                    logger.info(
                        f"📈 Network: {network_usage['mb_transferred']}MB transferred "
                        f"({network_usage['transfer_rate_mbps']} MB/s)"
                    )
                    
                    # Check if suspicious
                    if self.detect_suspicious_activity(network_usage):
                        # Get active connections for context
                        connections = self.get_active_connections()
                        
                        # Prepare activity data for API
                        activity_data = {
                            "user_id": self.user_config['user_id'],
                            "activity_type": "network_activity",
                            "timestamp": datetime.now().isoformat(),
                            "file_size": int(network_usage['bytes_transferred']),
                            "bytes_transferred": int(network_usage['bytes_transferred']),
                            "transfer_rate_mbps": network_usage['transfer_rate_mbps'],
                            "active_connections": len(connections),
                            "department": self.user_config['department'],
                            "role": self.user_config['role']
                        }
                        
                        # Send to API
                        logger.info("📤 Sending suspicious activity to API...")
                        self.send_to_api(activity_data)
                    
                    # Update baseline for next check
                    net_stats = psutil.net_io_counters()
                    self.baseline_bytes = net_stats.bytes_sent + net_stats.bytes_recv
                    self.last_check_time = time.time()
                
                # Wait before next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Monitoring stopped by user")
            self.monitoring_active = False
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
            self.monitoring_active = False
    
    def start_monitoring(self, interval: int = 30):
        """
        Start the network monitoring
        
        Args:
            interval: Check interval in seconds
        """
        self.monitor_loop(interval)
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring_active = False
        logger.info("🛑 Monitoring stopped")

# Standalone script mode
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("IGNISYL - Real-time Network Monitor")
    print("=" * 60)
    print()
    
    # Create monitor instance
    monitor = NetworkMonitor()
    
    # Start monitoring (checks every 30 seconds)
    try:
        monitor.start_monitoring(interval=30)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()