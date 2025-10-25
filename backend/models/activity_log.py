"""
Activity Logging System
Stores all detected threats and user activities in database
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json

class ActivityLogger:
    """Manages activity logs and threat history"""
    
    def __init__(self, db_path: str = "data/activities.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create activities table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                full_name TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                action TEXT NOT NULL,
                bytes_transferred INTEGER,
                file_size INTEGER,
                summary TEXT,
                details TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Activity logging database initialized")
    
    def log_activity(self, activity_data: Dict) -> int:
        """
        Log a detected activity/threat
        
        Args:
            activity_data: Dict with activity information
            
        Returns:
            Activity ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO activities (
                user_id, username, full_name, activity_type, 
                timestamp, risk_score, risk_level, action,
                bytes_transferred, file_size, summary, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            activity_data.get('user_id'),
            activity_data.get('username'),
            activity_data.get('full_name'),
            activity_data.get('activity_type'),
            activity_data.get('timestamp'),
            activity_data.get('risk_score'),
            activity_data.get('risk_level'),
            activity_data.get('action'),
            activity_data.get('bytes_transferred'),
            activity_data.get('file_size'),
            activity_data.get('summary'),
            json.dumps(activity_data.get('details', {}))
        ))
        
        activity_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return activity_id
    
    def get_recent_activities(self, limit: int = 10) -> List[Dict]:
        """Get most recent activities"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM activities 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        columns = [description[0] for description in cursor.description]
        activities = []
        
        for row in cursor.fetchall():
            activity = dict(zip(columns, row))
            if activity['details']:
                activity['details'] = json.loads(activity['details'])
            activities.append(activity)
        
        conn.close()
        return activities
    
    def get_user_activities(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get activities for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM activities 
            WHERE user_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (user_id, limit))
        
        columns = [description[0] for description in cursor.description]
        activities = []
        
        for row in cursor.fetchall():
            activity = dict(zip(columns, row))
            if activity['details']:
                activity['details'] = json.loads(activity['details'])
            activities.append(activity)
        
        conn.close()
        return activities
    
    def get_stats(self) -> Dict:
        """Get activity statistics"""
        conn = sqlite3.connect(self.db_path)
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
        
        conn.close()
        
        return {
            "total_activities": total_activities,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
            "blocked": blocked,
            "today": today_count
        }

# Global instance
activity_logger = ActivityLogger()