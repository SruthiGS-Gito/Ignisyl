"""
Activity Logging System
Stores all detected threats and user activities in database
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import json

class ActivityLogger:
    """Manages activity logs and threat history"""

    def __init__(self, db_path: str = None):
        # Use absolute path like user_management.py for consistency
        if db_path is None:
            backend_dir = Path(__file__).parent.parent.resolve()
            self.db_path = str(backend_dir / "data" / "activities.db")
        else:
            self.db_path = db_path

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        print(f"[ACTIVITY] Using database: {self.db_path}")
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
        print("[OK] Activity logging database initialized")
    
    def log_activity(self, activity_data: Dict) -> int:
        """
        Log a detected activity/threat with deduplication.

        Prevents duplicate entries for the same user + activity_type + risk_score
        within a 30-second window (to handle race conditions and duplicate events).

        Args:
            activity_data: Dict with activity information

        Returns:
            Activity ID (existing if duplicate, new if unique)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        user_id = activity_data.get('user_id')
        activity_type = activity_data.get('activity_type')
        risk_score = activity_data.get('risk_score')
        timestamp = activity_data.get('timestamp', datetime.now().isoformat())

        # DEDUPLICATION CHECK: Look for similar activity in same minute
        # Use minute-level comparison to catch rapid duplicate submissions
        timestamp_minute = timestamp[:16]  # YYYY-MM-DDTHH:MM
        try:
            cursor.execute("""
                SELECT id FROM activities
                WHERE user_id = ?
                AND activity_type = ?
                AND CAST(risk_score AS INTEGER) = CAST(? AS INTEGER)
                AND substr(timestamp, 1, 16) = ?
                LIMIT 1
            """, (user_id, activity_type, risk_score, timestamp_minute))

            existing = cursor.fetchone()
            if existing:
                conn.close()
                print(f"[DEDUP] Skipped duplicate activity: {user_id} - {activity_type} - {risk_score}")
                return existing[0]  # Return existing activity ID
        except Exception as e:
            print(f"[WARN] Deduplication check failed: {e}")

        # No duplicate found, insert new activity
        cursor.execute("""
            INSERT INTO activities (
                user_id, username, full_name, activity_type,
                timestamp, risk_score, risk_level, action,
                bytes_transferred, file_size, summary, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            activity_data.get('username'),
            activity_data.get('full_name'),
            activity_type,
            timestamp,
            risk_score,
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
        """Get activity statistics with consistent threat counting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total activities
        cursor.execute("SELECT COUNT(*) FROM activities")
        total_activities = cursor.fetchone()[0]

        # CRITICAL risk count (risk_level = 'CRITICAL' OR risk_score > 75)
        cursor.execute("SELECT COUNT(*) FROM activities WHERE risk_level = 'CRITICAL' OR risk_score > 75")
        critical_risk = cursor.fetchone()[0]

        # High risk count (risk_level = 'HIGH' or 51 <= risk_score <= 75)
        cursor.execute("SELECT COUNT(*) FROM activities WHERE risk_level = 'HIGH' AND risk_score <= 75")
        high_risk = cursor.fetchone()[0]

        # Medium risk count (31 <= risk_score <= 50)
        cursor.execute("SELECT COUNT(*) FROM activities WHERE risk_level = 'MEDIUM' OR (risk_score > 30 AND risk_score <= 50)")
        medium_risk = cursor.fetchone()[0]

        # Low risk count (risk_score <= 30)
        cursor.execute("SELECT COUNT(*) FROM activities WHERE risk_level = 'LOW' OR risk_score <= 30")
        low_risk = cursor.fetchone()[0]

        # Blocked actions (unique user blocks)
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM activities WHERE action = 'BLOCK'")
        blocked_users = cursor.fetchone()[0]

        # Total blocked actions
        cursor.execute("SELECT COUNT(*) FROM activities WHERE action = 'BLOCK'")
        blocked = cursor.fetchone()[0]

        # Threats detected = HIGH + CRITICAL (activities requiring attention)
        cursor.execute("SELECT COUNT(*) FROM activities WHERE risk_level IN ('HIGH', 'CRITICAL') OR risk_score > 50")
        threats_detected = cursor.fetchone()[0]

        # Active threats (not yet blocked, risk >= 50)
        cursor.execute("""
            SELECT COUNT(*) FROM activities
            WHERE (risk_level IN ('HIGH', 'CRITICAL') OR risk_score >= 50)
            AND action != 'BLOCK'
        """)
        active_threats = cursor.fetchone()[0]

        # Activities today
        today = datetime.now().date().isoformat()
        cursor.execute("SELECT COUNT(*) FROM activities WHERE DATE(timestamp) = ?", (today,))
        today_count = cursor.fetchone()[0]

        # Threats today
        cursor.execute("""
            SELECT COUNT(*) FROM activities
            WHERE DATE(timestamp) = ?
            AND (risk_level IN ('HIGH', 'CRITICAL') OR risk_score > 50)
        """, (today,))
        threats_today = cursor.fetchone()[0]

        conn.close()

        return {
            "total_activities": total_activities,
            "critical_risk": critical_risk,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
            "blocked": blocked,
            "blocked_users": blocked_users,
            "threats_detected": threats_detected,
            "active_threats": active_threats,
            "threats_today": threats_today,
            "today": today_count
        }

    def clear_all_activities(self):
        """Clear all activities from the database (for regeneration)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM activities")
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        print(f"[OK] Cleared {deleted} activities from database")
        return deleted

# Global instance
activity_logger = ActivityLogger()