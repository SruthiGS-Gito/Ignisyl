"""
Alert Management System for IGNISYL
Manages threat alerts, notifications, and alert prioritization
Integrates with database for persistence
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging
from enum import Enum

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from config.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AlertType(Enum):
    """Types of security alerts"""
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    PRIVILEGE_ABUSE = "PRIVILEGE_ABUSE"
    UNUSUAL_ACCESS = "UNUSUAL_ACCESS"
    AFTER_HOURS = "AFTER_HOURS"
    SUSPICIOUS_LOCATION = "SUSPICIOUS_LOCATION"
    LARGE_TRANSFER = "LARGE_TRANSFER"
    MULTIPLE_FAILURES = "MULTIPLE_FAILURES"
    INSIDER_THREAT = "INSIDER_THREAT"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"

class AlertManager:
    """
    Manages security alerts and notifications
    Persists to database for reliability
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = os.path.join(settings.DATA_PATH, "ignisyl.db")
        else:
            self.db_path = db_path
        
        self.alert_thresholds = {
            AlertPriority.LOW: 30,
            AlertPriority.MEDIUM: 50,
            AlertPriority.HIGH: 70,
            AlertPriority.CRITICAL: 90
        }
    
    def create_alert(self, alert_data: Dict) -> Optional[Dict]:
        """
        Create a new security alert
        
        Args:
            alert_data: Dictionary with alert information
                - user_id: User ID
                - alert_type: Type of alert
                - risk_score: Risk score (0-100)
                - description: Alert description
                - details: Additional details (dict)
            
        Returns:
            Created alert with ID or None
        """
        try:
            severity = self._calculate_priority(alert_data.get("risk_score", 0))
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO alerts (
                        user_id, alert_type, severity, title, description, alert_data
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    alert_data.get("user_id"),
                    alert_data.get("alert_type", AlertType.UNUSUAL_ACCESS.value),
                    severity,
                    alert_data.get("title", "Security Alert"),
                    alert_data.get("description", "Suspicious activity detected"),
                    json.dumps(alert_data.get("details", {}))
                ))
                
                alert_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"🚨 Alert {alert_id} created - Severity: {severity} - User: {alert_data.get('user_id')}")
                
                # Return full alert
                return self.get_alert(alert_id)
                
        except Exception as e:
            logger.error(f"❌ Failed to create alert: {e}")
            return None
    
    def _calculate_priority(self, risk_score: float) -> str:
        """Calculate alert severity based on risk score"""
        if risk_score >= self.alert_thresholds[AlertPriority.CRITICAL]:
            return AlertPriority.CRITICAL.value
        elif risk_score >= self.alert_thresholds[AlertPriority.HIGH]:
            return AlertPriority.HIGH.value
        elif risk_score >= self.alert_thresholds[AlertPriority.MEDIUM]:
            return AlertPriority.MEDIUM.value
        else:
            return AlertPriority.LOW.value
    
    def get_alert(self, alert_id: int) -> Optional[Dict]:
        """Get alert by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT a.*, u.username, u.full_name, u.department
                    FROM alerts a
                    LEFT JOIN users u ON a.user_id = u.id
                    WHERE a.id = ?
                """, (alert_id,))
                
                row = cursor.fetchone()
                
                if row:
                    alert = dict(row)
                    
                    # Parse JSON field
                    if alert.get('alert_data'):
                        try:
                            alert['alert_data'] = json.loads(alert['alert_data'])
                        except:
                            alert['alert_data'] = {}
                    
                    return alert
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get alert: {e}")
            return None
    
    def get_active_alerts(self, severity: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Get active (unresolved) alerts
        
        Args:
            severity: Optional severity filter (LOW, MEDIUM, HIGH, CRITICAL)
            limit: Max number of alerts
            
        Returns:
            List of active alerts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if severity:
                    cursor.execute("""
                        SELECT a.*, u.username, u.full_name, u.department
                        FROM alerts a
                        LEFT JOIN users u ON a.user_id = u.id
                        WHERE a.is_resolved = 0 AND a.severity = ?
                        ORDER BY a.created_at DESC
                        LIMIT ?
                    """, (severity, limit))
                else:
                    cursor.execute("""
                        SELECT a.*, u.username, u.full_name, u.department
                        FROM alerts a
                        LEFT JOIN users u ON a.user_id = u.id
                        WHERE a.is_resolved = 0
                        ORDER BY a.created_at DESC
                        LIMIT ?
                    """, (limit,))
                
                alerts = []
                for row in cursor.fetchall():
                    alert = dict(row)
                    
                    if alert.get('alert_data'):
                        try:
                            alert['alert_data'] = json.loads(alert['alert_data'])
                        except:
                            alert['alert_data'] = {}
                    
                    alerts.append(alert)
                
                return alerts
                
        except Exception as e:
            logger.error(f"❌ Failed to get active alerts: {e}")
            return []
    
    def get_critical_alerts(self, limit: int = 20) -> List[Dict]:
        """Get critical severity alerts"""
        return self.get_active_alerts(severity=AlertPriority.CRITICAL.value, limit=limit)
    
    def get_user_alerts(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get all alerts for a specific user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM alerts 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user_id, limit))
                
                alerts = []
                for row in cursor.fetchall():
                    alert = dict(row)
                    
                    if alert.get('alert_data'):
                        try:
                            alert['alert_data'] = json.loads(alert['alert_data'])
                        except:
                            pass
                    
                    alerts.append(alert)
                
                return alerts
                
        except Exception as e:
            logger.error(f"❌ Failed to get user alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """
        Mark an alert as acknowledged
        
        Args:
            alert_id: Alert ID
            acknowledged_by: Username of person acknowledging
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE alerts 
                    SET is_acknowledged = 1,
                        acknowledged_by = ?,
                        acknowledged_at = ?
                    WHERE id = ?
                """, (acknowledged_by, datetime.now().isoformat(), alert_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Alert {alert_id} acknowledged by {acknowledged_by}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to acknowledge alert: {e}")
            return False
    
    def resolve_alert(self, alert_id: int, resolved_by: str, 
                     resolution_notes: str = "") -> bool:
        """
        Mark an alert as resolved
        
        Args:
            alert_id: Alert ID
            resolved_by: Username of person resolving
            resolution_notes: Optional resolution notes
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update alert data with resolution notes
                cursor.execute("SELECT alert_data FROM alerts WHERE id = ?", (alert_id,))
                row = cursor.fetchone()
                
                if row and row[0]:
                    try:
                        alert_data = json.loads(row[0])
                    except:
                        alert_data = {}
                else:
                    alert_data = {}
                
                alert_data['resolution_notes'] = resolution_notes
                
                cursor.execute("""
                    UPDATE alerts 
                    SET is_resolved = 1,
                        resolved_by = ?,
                        resolved_at = ?,
                        alert_data = ?
                    WHERE id = ?
                """, (resolved_by, datetime.now().isoformat(), 
                     json.dumps(alert_data), alert_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Alert {alert_id} resolved by {resolved_by}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to resolve alert: {e}")
            return False
    
    def get_alert_stats(self, days: int = 30) -> Dict:
        """
        Get alert statistics
        
        Args:
            days: Number of days to include
            
        Returns:
            Dictionary with statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
                
                stats = {}
                
                # Total alerts
                cursor.execute("""
                    SELECT COUNT(*) FROM alerts WHERE created_at >= ?
                """, (date_threshold,))
                stats['total_alerts'] = cursor.fetchone()[0]
                
                # Active alerts
                cursor.execute("SELECT COUNT(*) FROM alerts WHERE is_resolved = 0")
                stats['active_alerts'] = cursor.fetchone()[0]
                
                # Resolved alerts
                cursor.execute("""
                    SELECT COUNT(*) FROM alerts 
                    WHERE is_resolved = 1 AND created_at >= ?
                """, (date_threshold,))
                stats['resolved_alerts'] = cursor.fetchone()[0]
                
                # By severity
                priority_counts = {}
                for priority in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
                    cursor.execute("""
                        SELECT COUNT(*) FROM alerts 
                        WHERE severity = ? AND is_resolved = 0
                    """, (priority,))
                    priority_counts[priority.lower()] = cursor.fetchone()[0]
                
                stats['priority_breakdown'] = priority_counts
                
                # Acknowledged but not resolved
                cursor.execute("""
                    SELECT COUNT(*) FROM alerts 
                    WHERE is_acknowledged = 1 AND is_resolved = 0
                """)
                stats['acknowledged_pending'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Failed to get alert stats: {e}")
            return {}
    
    def clear_old_alerts(self, days: int = 90) -> int:
        """
        Delete resolved alerts older than specified days
        
        Args:
            days: Age threshold
            
        Returns:
            Number of alerts deleted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor.execute("""
                    DELETE FROM alerts
                    WHERE is_resolved = 1 AND resolved_at < ?
                """, (date_threshold,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"🗑️ Deleted {deleted_count} old resolved alerts")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Failed to clear old alerts: {e}")
            return 0

# Global instance
try:
    alert_manager = AlertManager()
except Exception as e:
    logger.error(f"Failed to initialize alert manager: {e}")
    alert_manager = None

def main():
    """Test alert manager functions"""
    print("\n" + "="*60)
    print("IGNISYL Alert Manager Test")
    print("="*60 + "\n")
    
    manager = AlertManager()
    
    # Get stats
    stats = manager.get_alert_stats()
    print("📊 Alert Statistics:")
    for key, value in stats.items():
        if key != 'priority_breakdown':
            print(f"   {key}: {value}")
    
    # Get active alerts
    active = manager.get_active_alerts(limit=5)
    print(f"\n⚠️ Active alerts: {len(active)}")
    
    # Get critical alerts
    critical = manager.get_critical_alerts()
    print(f"🚨 Critical alerts: {len(critical)}")
    
    print("\n✅ Alert manager test complete!")

if __name__ == "__main__":
    main()