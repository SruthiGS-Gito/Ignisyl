"""
Log Processing System for IGNISYL
Processes, analyzes, and aggregates system logs
Integrates with activity_logger for persistence
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import re
from collections import defaultdict
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from config.config import settings
from models.activity_logger import activity_logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogProcessor:
    """
    Processes and analyzes system logs
    Extracts patterns, generates insights, and aggregates data
    
    NOTE: This complements activity_logger by providing advanced analytics
    """
    
    def __init__(self):
        self.log_buffer = []
        self.log_patterns = self._initialize_patterns()
        
        logger.info("📊 Log Processor initialized")
    
    def _initialize_patterns(self) -> Dict:
        """Initialize regex patterns for log parsing"""
        return {
            "failed_login": re.compile(r"Failed login attempt.*user[:\s]+(\w+)", re.IGNORECASE),
            "data_access": re.compile(r"Data access.*file[:\s]+([\w\.]+)", re.IGNORECASE),
            "privilege_escalation": re.compile(r"Privilege.*elevated", re.IGNORECASE),
            "network_anomaly": re.compile(r"Network.*anomaly.*(\d+\.){3}\d+", re.IGNORECASE),
            "firewall_block": re.compile(r"Firewall.*blocked.*user[:\s]+(\w+)", re.IGNORECASE),
            "honeypot": re.compile(r"honeypot", re.IGNORECASE),
            "suspicious": re.compile(r"suspicious|threat|malicious|unauthorized", re.IGNORECASE)
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
        
        # Store in buffer (limited size)
        self.log_buffer.append(processed)
        
        # Keep buffer size manageable (last 10000 logs)
        if len(self.log_buffer) > 10000:
            self.log_buffer = self.log_buffer[-10000:]
        
        return processed
    
    def analyze_activities(self, hours: int = 24) -> Dict:
        """
        Analyze activities from database
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Analysis results with insights
        """
        try:
            # Get recent activities from database
            activities = activity_logger.get_recent_activities(limit=1000)
            
            # Filter by time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent = [
                a for a in activities
                if datetime.fromisoformat(a.get('timestamp', '')) > cutoff_time
            ]
            
            # Analyze
            level_counts = defaultdict(int)
            user_counts = defaultdict(int)
            risk_distribution = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
            
            for activity in recent:
                level_counts[activity.get('risk_level', 'UNKNOWN')] += 1
                user_id = activity.get('user_id')
                if user_id:
                    user_counts[user_id] += 1
                
                risk_level = activity.get('risk_level', 'LOW')
                if risk_level in risk_distribution:
                    risk_distribution[risk_level] += 1
            
            # Find suspicious users (high activity count)
            suspicious_users = [
                user_id for user_id, count in user_counts.items()
                if count > 20  # More than 20 activities in time window
            ]
            
            return {
                "time_window_hours": hours,
                "total_activities": len(recent),
                "risk_distribution": risk_distribution,
                "level_distribution": dict(level_counts),
                "user_activity": dict(user_counts),
                "suspicious_users": suspicious_users,
                "high_risk_count": level_counts['HIGH'] + level_counts.get('CRITICAL', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze activities: {e}")
            return {}
    
    def get_user_activity_summary(self, user_id: int, days: int = 7) -> Dict:
        """
        Get activity summary for a user
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            User activity summary
        """
        try:
            activities = activity_logger.get_user_activities(user_id, limit=500)
            
            cutoff_time = datetime.now() - timedelta(days=days)
            recent = [
                a for a in activities
                if datetime.fromisoformat(a.get('timestamp', '')) > cutoff_time
            ]
            
            # Analyze activity types
            type_counts = defaultdict(int)
            risk_scores = []
            
            for activity in recent:
                type_counts[activity.get('activity_type', 'unknown')] += 1
                risk_scores.append(activity.get('risk_score', 0))
            
            return {
                "user_id": user_id,
                "days_analyzed": days,
                "total_activities": len(recent),
                "activity_types": dict(type_counts),
                "average_risk_score": sum(risk_scores) / len(risk_scores) if risk_scores else 0,
                "max_risk_score": max(risk_scores) if risk_scores else 0,
                "high_risk_activities": len([s for s in risk_scores if s >= 70])
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get user summary: {e}")
            return {}
    
    def detect_anomaly_patterns(self, hours: int = 24) -> List[Dict]:
        """
        Detect anomalous patterns in activities
        
        Args:
            hours: Time window to analyze
            
        Returns:
            List of detected anomalies
        """
        try:
            activities = activity_logger.get_recent_activities(limit=1000)
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent = [
                a for a in activities
                if datetime.fromisoformat(a.get('timestamp', '')) > cutoff_time
            ]
            
            anomalies = []
            
            # Check for rapid successive activities
            user_activity_times = defaultdict(list)
            for activity in recent:
                user_id = activity.get('user_id')
                timestamp = datetime.fromisoformat(activity.get('timestamp', ''))
                user_activity_times[user_id].append(timestamp)
            
            for user_id, timestamps in user_activity_times.items():
                if len(timestamps) < 2:
                    continue
                
                timestamps.sort()
                
                # Check for rapid succession (>5 activities in 5 minutes)
                for i in range(len(timestamps) - 4):
                    time_span = (timestamps[i+4] - timestamps[i]).total_seconds()
                    if time_span < 300:  # 5 minutes
                        anomalies.append({
                            'type': 'rapid_succession',
                            'user_id': user_id,
                            'description': f'User {user_id} had 5+ activities in {time_span:.0f} seconds',
                            'severity': 'MEDIUM',
                            'timestamp': timestamps[i].isoformat()
                        })
                        break
            
            return anomalies
            
        except Exception as e:
            logger.error(f"❌ Failed to detect anomalies: {e}")
            return []
    
    def export_activities(self, filepath: str, days: int = 7) -> int:
        """
        Export activities to file
        
        Args:
            filepath: Path to export file
            days: Number of days to export
            
        Returns:
            Number of activities exported
        """
        try:
            activities = activity_logger.get_recent_activities(limit=10000)
            
            cutoff_time = datetime.now() - timedelta(days=days)
            recent = [
                a for a in activities
                if datetime.fromisoformat(a.get('timestamp', '')) > cutoff_time
            ]
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(recent, f, indent=2, default=str)
            
            logger.info(f"📄 Exported {len(recent)} activities to {filepath}")
            return len(recent)
            
        except Exception as e:
            logger.error(f"❌ Failed to export activities: {e}")
            return 0
    
    def get_stats(self) -> Dict:
        """Get log processor statistics"""
        stats = activity_logger.get_stats()
        
        return {
            'buffer_size': len(self.log_buffer),
            'patterns_tracked': len(self.log_patterns),
            'activities_today': stats.get('today', 0),
            'high_risk_activities': stats.get('high_risk', 0),
            'total_activities': stats.get('total_activities', 0)
        }

# Global instance
try:
    log_processor = LogProcessor()
except Exception as e:
    logger.error(f"Failed to initialize log processor: {e}")
    log_processor = None

def main():
    """Test log processor"""
    print("\n" + "="*60)
    print("IGNISYL Log Processor Test")
    print("="*60 + "\n")
    
    processor = LogProcessor()
    
    # Analyze recent activities
    print("Analyzing recent activities...")
    analysis = processor.analyze_activities(hours=24)
    
    print(f"\n📊 Analysis Results (last 24h):")
    for key, value in analysis.items():
        print(f"   {key}: {value}")
    
    # Detect anomalies
    anomalies = processor.detect_anomaly_patterns(hours=24)
    print(f"\n⚠️ Anomalies detected: {len(anomalies)}")
    
    # Get stats
    stats = processor.get_stats()
    print(f"\n📈 Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Log processor test complete!")

if __name__ == "__main__":
    main()