"""
Log Processing System for IGNISYL
Processes, analyzes, and aggregates system logs
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import re
from collections import defaultdict

class LogProcessor:
    """
    Processes and analyzes system logs
    Extracts patterns, generates insights, and aggregates data
    """
    
    def __init__(self):
        self.log_buffer = []
        self.processed_logs = []
        self.log_patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict:
        """Initialize regex patterns for log parsing"""
        return {
            "failed_login": re.compile(r"Failed login attempt.*user[:\s]+(\w+)", re.IGNORECASE),
            "data_access": re.compile(r"Data access.*file[:\s]+([\w\.]+)", re.IGNORECASE),
            "privilege_escalation": re.compile(r"Privilege.*elevated", re.IGNORECASE),
            "network_anomaly": re.compile(r"Network.*anomaly.*(\d+\.){3}\d+", re.IGNORECASE),
            "firewall_block": re.compile(r"Firewall.*blocked.*user[:\s]+(\w+)", re.IGNORECASE)
        }
    
    def process_log_entry(self, log_entry: Dict) -> Dict:
        """
        Process a single log entry
        
        Args:
            log_entry: Raw log entry dictionary
            
        Returns:
            Processed log entry with extracted metadata
        """
        processed = {
            "log_id": f"log_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "timestamp": log_entry.get("timestamp", datetime.now().isoformat()),
            "level": log_entry.get("level", "INFO"),
            "source": log_entry.get("source", "system"),
            "message": log_entry.get("message", ""),
            "user_id": log_entry.get("user_id"),
            "raw_data": log_entry
        }
        
        # Extract patterns from message
        message = processed["message"]
        detected_patterns = []
        
        for pattern_name, pattern_regex in self.log_patterns.items():
            if pattern_regex.search(message):
                detected_patterns.append(pattern_name)
        
        processed["detected_patterns"] = detected_patterns
        processed["is_suspicious"] = len(detected_patterns) > 0
        
        self.log_buffer.append(processed)
        self.processed_logs.append(processed)
        
        return processed
    
    def analyze_logs(self, time_window: int = 3600) -> Dict:
        """
        Analyze logs within a time window
        
        Args:
            time_window: Time window in seconds (default 1 hour)
            
        Returns:
            Analysis results with insights
        """
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        
        recent_logs = [
            log for log in self.processed_logs
            if datetime.fromisoformat(log["timestamp"]) > cutoff_time
        ]
        
        # Count by level
        level_counts = defaultdict(int)
        for log in recent_logs:
            level_counts[log["level"]] += 1
        
        # Count by pattern
        pattern_counts = defaultdict(int)
        for log in recent_logs:
            for pattern in log.get("detected_patterns", []):
                pattern_counts[pattern] += 1
        
        # Count by user
        user_counts = defaultdict(int)
        for log in recent_logs:
            if log.get("user_id"):
                user_counts[log["user_id"]] += 1
        
        # Identify suspicious users (high log volume)
        suspicious_users = [
            user_id for user_id, count in user_counts.items()
            if count > 50  # Threshold: more than 50 logs in time window
        ]
        
        analysis = {
            "time_window_seconds": time_window,
            "total_logs": len(recent_logs),
            "level_distribution": dict(level_counts),
            "pattern_distribution": dict(pattern_counts),
            "user_activity": dict(user_counts),
            "suspicious_users": suspicious_users,
            "suspicious_log_count": len([log for log in recent_logs if log["is_suspicious"]])
        }
        
        return analysis
    
    def get_user_logs(self, user_id: str, limit: int = 100) -> List[Dict]:
        """
        Get logs for a specific user
        
        Args:
            user_id: User ID to filter logs
            limit: Maximum number of logs to return
            
        Returns:
            List of user's logs
        """
        user_logs = [
            log for log in self.processed_logs
            if log.get("user_id") == user_id
        ]
        
        # Sort by timestamp, most recent first
        user_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return user_logs[:limit]
    
    def get_suspicious_logs(self, hours: int = 24) -> List[Dict]:
        """
        Get suspicious logs from recent hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of suspicious logs
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        suspicious = [
            log for log in self.processed_logs
            if log["is_suspicious"] and 
            datetime.fromisoformat(log["timestamp"]) > cutoff_time
        ]
        
        return suspicious
    
    def detect_patterns(self, pattern_name: str, time_window: int = 3600) -> List[Dict]:
        """
        Detect specific patterns in recent logs
        
        Args:
            pattern_name: Name of pattern to detect
            time_window: Time window in seconds
            
        Returns:
            Logs matching the pattern
        """
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        
        matching_logs = [
            log for log in self.processed_logs
            if pattern_name in log.get("detected_patterns", []) and
            datetime.fromisoformat(log["timestamp"]) > cutoff_time
        ]
        
        return matching_logs
    
    def aggregate_by_time(self, interval: str = "hour") -> Dict:
        """
        Aggregate logs by time interval
        
        Args:
            interval: "hour", "day", or "week"
            
        Returns:
            Aggregated log counts by time interval
        """
        aggregated = defaultdict(int)
        
        for log in self.processed_logs:
            timestamp = datetime.fromisoformat(log["timestamp"])
            
            if interval == "hour":
                key = timestamp.strftime("%Y-%m-%d %H:00")
            elif interval == "day":
                key = timestamp.strftime("%Y-%m-%d")
            elif interval == "week":
                key = f"{timestamp.year}-W{timestamp.isocalendar()[1]}"
            else:
                key = timestamp.strftime("%Y-%m-%d")
            
            aggregated[key] += 1
        
        return dict(aggregated)
    
    def export_logs(self, filepath: str, start_time: Optional[str] = None, 
                   end_time: Optional[str] = None) -> int:
        """
        Export logs to file
        
        Args:
            filepath: Path to export file
            start_time: Optional start time filter (ISO format)
            end_time: Optional end time filter (ISO format)
            
        Returns:
            Number of logs exported
        """
        logs_to_export = self.processed_logs
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            logs_to_export = [
                log for log in logs_to_export
                if datetime.fromisoformat(log["timestamp"]) >= start_dt
            ]
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time)
            logs_to_export = [
                log for log in logs_to_export
                if datetime.fromisoformat(log["timestamp"]) <= end_dt
            ]
        
        with open(filepath, 'w') as f:
            json.dump(logs_to_export, f, indent=2, default=str)
        
        print(f"[*] Exported {len(logs_to_export)} logs to {filepath}")
        
        return len(logs_to_export)
    
    def clear_old_logs(self, days_old: int = 90) -> int:
        """
        Clear logs older than specified days
        
        Args:
            days_old: Remove logs older than this many days
            
        Returns:
            Number of logs cleared
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        initial_count = len(self.processed_logs)
        self.processed_logs = [
            log for log in self.processed_logs
            if datetime.fromisoformat(log["timestamp"]) > cutoff_date
        ]
        
        cleared_count = initial_count - len(self.processed_logs)
        
        if cleared_count > 0:
            print(f"[DEL] Cleared {cleared_count} old logs")
        
        return cleared_count

# Global instance
log_processor = LogProcessor()