"""
User Activity Tracking Module for IGNISYL
Records and retrieves user activities
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from config.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserActivityManager:
    """Manages user activity logging and retrieval"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = os.path.join(settings.DATA_PATH, "ignisyl.db")
        else:
            self.db_path = db_path
    
    def log_activity(self, user_id: int, activity_type: str, 
                    activity_data: Dict) -> Optional[int]:
        """
        Log a user activity
        
        Args:
            user_id: User ID
            activity_type: Type of activity (login, file_access, etc.)
            activity_data: Activity details
            
        Returns:
            Activity ID or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO user_activities (
                        user_id, activity_type, activity_details,
                        source_ip, destination_ip, user_agent, device_info,
                        file_path, file_size, network_bytes, protocol,
                        timestamp, is_suspicious, confidence_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    activity_type,
                    json.dumps(activity_data),
                    activity_data.get('source_ip', ''),
                    activity_data.get('destination_ip', ''),
                    activity_data.get('user_agent', ''),
                    activity_data.get('device_info', ''),
                    activity_data.get('file_path', ''),
                    activity_data.get('file_size', 0),
                    activity_data.get('network_bytes', 0),
                    activity_data.get('protocol', ''),
                    activity_data.get('timestamp', datetime.now().isoformat()),
                    int(activity_data.get('is_suspicious', False)),
                    activity_data.get('confidence_score', 0.0)
                ))
                
                activity_id = cursor.lastrowid
                conn.commit()
                
                logger.debug(f"Logged activity {activity_id} for user {user_id}")
                return activity_id
                
        except Exception as e:
            logger.error(f"❌ Failed to log activity: {e}")
            return None
    
    def get_activity(self, activity_id: int) -> Optional[Dict]:
        """Get activity by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM user_activities WHERE id = ?
                """, (activity_id,))
                
                row = cursor.fetchone()
                
                if row:
                    activity = dict(row)
                    
                    # Parse activity_details JSON
                    if activity.get('activity_details'):
                        try:
                            activity['activity_details'] = json.loads(activity['activity_details'])
                        except:
                            activity['activity_details'] = {}
                    
                    return activity
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get activity: {e}")
            return None
    
    def get_user_activities(self, user_id: int, limit: int = 100, 
                           activity_type: Optional[str] = None) -> List[Dict]:
        """
        Get activities for a user
        
        Args:
            user_id: User ID
            limit: Max number of activities
            activity_type: Filter by activity type (optional)
            
        Returns:
            List of activity dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if activity_type:
                    cursor.execute("""
                        SELECT * FROM user_activities 
                        WHERE user_id = ? AND activity_type = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (user_id, activity_type, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM user_activities 
                        WHERE user_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (user_id, limit))
                
                activities = []
                for row in cursor.fetchall():
                    activity = dict(row)
                    
                    # Parse JSON
                    if activity.get('activity_details'):
                        try:
                            activity['activity_details'] = json.loads(activity['activity_details'])
                        except:
                            activity['activity_details'] = {}
                    
                    activities.append(activity)
                
                return activities
                
        except Exception as e:
            logger.error(f"❌ Failed to get user activities: {e}")
            return []
    
    def get_suspicious_activities(self, limit: int = 50) -> List[Dict]:
        """Get suspicious activities"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT ua.*, u.username, u.full_name, u.department
                    FROM user_activities ua
                    LEFT JOIN users u ON ua.user_id = u.id
                    WHERE ua.is_suspicious = 1
                    ORDER BY ua.timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                activities = []
                for row in cursor.fetchall():
                    activity = dict(row)
                    
                    if activity.get('activity_details'):
                        try:
                            activity['activity_details'] = json.loads(activity['activity_details'])
                        except:
                            pass
                    
                    activities.append(activity)
                
                return activities
                
        except Exception as e:
            logger.error(f"❌ Failed to get suspicious activities: {e}")
            return []
    
    def get_recent_activities(self, limit: int = 50, minutes: int = 60) -> List[Dict]:
        """Get recent activities within time window"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                time_threshold = (datetime.now() - timedelta(minutes=minutes)).isoformat()
                
                cursor.execute("""
                    SELECT ua.*, u.username, u.full_name
                    FROM user_activities ua
                    LEFT JOIN users u ON ua.user_id = u.id
                    WHERE ua.timestamp >= ?
                    ORDER BY ua.timestamp DESC
                    LIMIT ?
                """, (time_threshold, limit))
                
                activities = []
                for row in cursor.fetchall():
                    activity = dict(row)
                    
                    if activity.get('activity_details'):
                        try:
                            activity['activity_details'] = json.loads(activity['activity_details'])
                        except:
                            pass
                    
                    activities.append(activity)
                
                return activities
                
        except Exception as e:
            logger.error(f"❌ Failed to get recent activities: {e}")
            return []
    
    def get_activity_stats(self, days: int = 7) -> Dict:
        """Get activity statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
                
                stats = {}
                
                # Total activities
                cursor.execute("""
                    SELECT COUNT(*) FROM user_activities 
                    WHERE timestamp >= ?
                """, (date_threshold,))
                stats['total_activities'] = cursor.fetchone()[0]
                
                # Suspicious activities
                cursor.execute("""
                    SELECT COUNT(*) FROM user_activities 
                    WHERE is_suspicious = 1 AND timestamp >= ?
                """, (date_threshold,))
                stats['suspicious_activities'] = cursor.fetchone()[0]
                
                # By activity type
                cursor.execute("""
                    SELECT activity_type, COUNT(*) as count
                    FROM user_activities
                    WHERE timestamp >= ?
                    GROUP BY activity_type
                    ORDER BY count DESC
                """, (date_threshold,))
                
                stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Most active users
                cursor.execute("""
                    SELECT u.username, u.full_name, COUNT(*) as count
                    FROM user_activities ua
                    LEFT JOIN users u ON ua.user_id = u.id
                    WHERE ua.timestamp >= ?
                    GROUP BY ua.user_id
                    ORDER BY count DESC
                    LIMIT 5
                """, (date_threshold,))
                
                stats['most_active_users'] = [
                    {'username': row[0], 'full_name': row[1], 'activity_count': row[2]}
                    for row in cursor.fetchall()
                ]
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Failed to get activity stats: {e}")
            return {}
    
    def delete_old_activities(self, days: int = 90) -> int:
        """Delete activities older than specified days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor.execute("""
                    DELETE FROM user_activities
                    WHERE timestamp < ?
                """, (date_threshold,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Deleted {deleted_count} activities older than {days} days")
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Failed to delete old activities: {e}")
            return 0

# Global instance
try:
    user_activity_manager = UserActivityManager()
except Exception as e:
    logger.error(f"Failed to initialize user activity manager: {e}")
    user_activity_manager = None

def main():
    """Test user activity functions"""
    print("\n" + "="*60)
    print("IGNISYL User Activity Test")
    print("="*60 + "\n")
    
    manager = UserActivityManager()
    
    # Get stats
    stats = manager.get_activity_stats(days=30)
    print("📊 Activity Statistics (last 30 days):")
    for key, value in stats.items():
        if key != 'by_type' and key != 'most_active_users':
            print(f"   {key}: {value}")
    
    # Get suspicious activities
    suspicious = manager.get_suspicious_activities(limit=5)
    print(f"\n⚠️ Suspicious activities: {len(suspicious)}")
    
    print("\n✅ User activity test complete!")

if __name__ == "__main__":
    main()