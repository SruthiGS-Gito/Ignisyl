"""
Activity Logging System for IGNISYL
Stores all detected threats and user activities in database
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActivityLogger:
    """Manages activity logs and threat history"""
    
    def __init__(self, db_path: Optional[str] = None):
        # Use proper path from config
        if db_path is None:
            from config.config import settings
            os.makedirs(settings.DATA_PATH, exist_ok=True)
            self.db_path = os.path.join(settings.DATA_PATH, "activities.db")
        else:
            self.db_path = db_path
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Create activities table if it doesn't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        username TEXT NOT NULL,
                        full_name TEXT,
                        department TEXT,
                        activity_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        risk_score REAL NOT NULL,
                        risk_level TEXT NOT NULL,
                        action TEXT NOT NULL,
                        bytes_transferred INTEGER,
                        file_size INTEGER,
                        source_ip TEXT,
                        destination_ip TEXT,
                        summary TEXT,
                        details TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better query performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_id ON activities(user_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON activities(timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_risk_level ON activities(risk_level)
                """)
                
                conn.commit()
                logger.info(f"✅ Activity database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    def log_activity(self, activity_data: Dict) -> Optional[int]:
        """
        Log a detected activity/threat
        
        Args:
            activity_data: Dict with activity information
            
        Returns:
            Activity ID or None if failed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO activities (
                        user_id, username, full_name, department, activity_type, 
                        timestamp, risk_score, risk_level, action,
                        bytes_transferred, file_size, source_ip, destination_ip,
                        summary, details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    activity_data.get('user_id', 'unknown'),
                    activity_data.get('username', 'unknown'),
                    activity_data.get('full_name', ''),
                    activity_data.get('department', ''),
                    activity_data.get('activity_type', 'unknown'),
                    activity_data.get('timestamp', datetime.now().isoformat()),
                    activity_data.get('risk_score', 0.0),
                    activity_data.get('risk_level', 'LOW'),
                    activity_data.get('action', 'ALLOW'),
                    activity_data.get('bytes_transferred', 0),
                    activity_data.get('file_size', 0),
                    activity_data.get('source_ip', ''),
                    activity_data.get('destination_ip', ''),
                    activity_data.get('summary', ''),
                    json.dumps(activity_data.get('details', {}))
                ))
                
                activity_id = cursor.lastrowid
                conn.commit()
                
                logger.debug(f"Logged activity {activity_id} for user {activity_data.get('user_id')}")
                return activity_id
                
        except Exception as e:
            logger.error(f"❌ Failed to log activity: {e}")
            return None
    
    def get_recent_activities(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        """
        Get most recent activities with pagination
        
        Args:
            limit: Number of activities to return
            offset: Number of activities to skip
            
        Returns:
            List of activity dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM activities 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                columns = [description[0] for description in cursor.description]
                activities = []
                
                for row in cursor.fetchall():
                    activity = dict(zip(columns, row))
                    if activity.get('details'):
                        try:
                            activity['details'] = json.loads(activity['details'])
                        except json.JSONDecodeError:
                            activity['details'] = {}
                    activities.append(activity)
                
                return activities
                
        except Exception as e:
            logger.error(f"❌ Failed to get recent activities: {e}")
            return []
    
    def get_user_activities(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Get activities for a specific user
        
        Args:
            user_id: User identifier
            limit: Number of activities to return
            offset: Number of activities to skip
            
        Returns:
            List of activity dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM activities 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
                
                columns = [description[0] for description in cursor.description]
                activities = []
                
                for row in cursor.fetchall():
                    activity = dict(zip(columns, row))
                    if activity.get('details'):
                        try:
                            activity['details'] = json.loads(activity['details'])
                        except json.JSONDecodeError:
                            activity['details'] = {}
                    activities.append(activity)
                
                return activities
                
        except Exception as e:
            logger.error(f"❌ Failed to get user activities: {e}")
            return []
    
    def get_high_risk_activities(self, limit: int = 20) -> List[Dict]:
        """Get recent high-risk activities"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM activities 
                    WHERE risk_level = 'HIGH'
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                columns = [description[0] for description in cursor.description]
                activities = []
                
                for row in cursor.fetchall():
                    activity = dict(zip(columns, row))
                    if activity.get('details'):
                        try:
                            activity['details'] = json.loads(activity['details'])
                        except json.JSONDecodeError:
                            activity['details'] = {}
                    activities.append(activity)
                
                return activities
                
        except Exception as e:
            logger.error(f"❌ Failed to get high-risk activities: {e}")
            return []
    
    def get_stats(self, days: int = 30) -> Dict:
        """
        Get activity statistics
        
        Args:
            days: Number of days to include in stats
            
        Returns:
            Dictionary with statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total activities
                cursor.execute("SELECT COUNT(*) FROM activities")
                total_activities = cursor.fetchone()[0]
                
                # High risk count
                cursor.execute("SELECT COUNT(*) FROM activities WHERE risk_level = 'HIGH'")
                high_risk = cursor.fetchone()[0]
                
                # Medium risk count
                cursor.execute("SELECT COUNT(*) FROM activities WHERE risk_level = 'MEDIUM'")
                medium_risk = cursor.fetchone()[0]
                
                # Low risk count
                cursor.execute("SELECT COUNT(*) FROM activities WHERE risk_level = 'LOW'")
                low_risk = cursor.fetchone()[0]
                
                # Blocked actions
                cursor.execute("SELECT COUNT(*) FROM activities WHERE action = 'BLOCK'")
                blocked = cursor.fetchone()[0]
                
                # Activities today
                today = datetime.now().date().isoformat()
                cursor.execute("SELECT COUNT(*) FROM activities WHERE DATE(timestamp) = ?", (today,))
                today_count = cursor.fetchone()[0]
                
                # Activities in last N days
                date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
                cursor.execute("""
                    SELECT COUNT(*) FROM activities 
                    WHERE timestamp >= ?
                """, (date_threshold,))
                recent_count = cursor.fetchone()[0]
                
                # Average risk score
                cursor.execute("SELECT AVG(risk_score) FROM activities")
                avg_risk = cursor.fetchone()[0] or 0.0
                
                # Top risky users
                cursor.execute("""
                    SELECT user_id, username, COUNT(*) as count, AVG(risk_score) as avg_risk
                    FROM activities
                    WHERE risk_level IN ('HIGH', 'MEDIUM')
                    GROUP BY user_id
                    ORDER BY avg_risk DESC
                    LIMIT 5
                """)
                
                top_risky_users = []
                for row in cursor.fetchall():
                    top_risky_users.append({
                        'user_id': row[0],
                        'username': row[1],
                        'incident_count': row[2],
                        'avg_risk_score': round(row[3], 2)
                    })
                
                return {
                    "total_activities": total_activities,
                    "high_risk": high_risk,
                    "medium_risk": medium_risk,
                    "low_risk": low_risk,
                    "blocked": blocked,
                    "today": today_count,
                    f"last_{days}_days": recent_count,
                    "average_risk_score": round(avg_risk, 2),
                    "top_risky_users": top_risky_users
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {
                "total_activities": 0,
                "high_risk": 0,
                "medium_risk": 0,
                "low_risk": 0,
                "blocked": 0,
                "today": 0,
                f"last_{days}_days": 0,
                "average_risk_score": 0.0,
                "top_risky_users": []
            }
    
    def get_activity_timeline(self, days: int = 7) -> List[Dict]:
        """
        Get activity timeline for charts
        
        Args:
            days: Number of days to include
            
        Returns:
            List of daily activity counts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                date_threshold = (datetime.now() - timedelta(days=days)).date().isoformat()
                
                cursor.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as total,
                        SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_risk,
                        SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_risk,
                        SUM(CASE WHEN risk_level = 'LOW' THEN 1 ELSE 0 END) as low_risk
                    FROM activities
                    WHERE DATE(timestamp) >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY DATE(timestamp)
                """, (date_threshold,))
                
                timeline = []
                for row in cursor.fetchall():
                    timeline.append({
                        'date': row[0],
                        'total': row[1],
                        'high_risk': row[2],
                        'medium_risk': row[3],
                        'low_risk': row[4]
                    })
                
                return timeline
                
        except Exception as e:
            logger.error(f"❌ Failed to get activity timeline: {e}")
            return []
    
    def clear_old_activities(self, days: int = 90) -> int:
        """
        Delete activities older than specified days
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of deleted records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor.execute("""
                    DELETE FROM activities
                    WHERE timestamp < ?
                """, (date_threshold,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Deleted {deleted_count} activities older than {days} days")
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Failed to clear old activities: {e}")
            return 0

# Global instance - initialize on import
try:
    activity_logger = ActivityLogger()
except Exception as e:
    logger.error(f"Failed to initialize activity logger: {e}")
    activity_logger = None