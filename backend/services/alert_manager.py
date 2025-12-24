"""
Alert Management System for IGNISYL
Manages threat alerts, notifications, and alert prioritization
"""

from datetime import datetime
from typing import Dict, List, Optional
import json
from enum import Enum

class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Types of security alerts"""
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ABUSE = "privilege_abuse"
    UNUSUAL_ACCESS = "unusual_access"
    AFTER_HOURS = "after_hours"
    SUSPICIOUS_LOCATION = "suspicious_location"
    LARGE_TRANSFER = "large_transfer"
    MULTIPLE_FAILURES = "multiple_failures"

class AlertManager:
    """
    Manages security alerts and notifications
    Handles alert creation, prioritization, and tracking
    """
    
    def __init__(self):
        self.active_alerts = []
        self.alert_history = []
        self.alert_thresholds = {
            AlertPriority.LOW: 30,
            AlertPriority.MEDIUM: 50,
            AlertPriority.HIGH: 70,
            AlertPriority.CRITICAL: 90
        }
    
    def create_alert(self, alert_data: Dict) -> Dict:
        """
        Create a new security alert
        
        Args:
            alert_data: Dictionary with alert information
            
        Returns:
            Created alert with ID and metadata
        """
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        alert = {
            "alert_id": alert_id,
            "timestamp": datetime.now().isoformat(),
            "user_id": alert_data.get("user_id"),
            "username": alert_data.get("username"),
            "alert_type": alert_data.get("alert_type", AlertType.UNUSUAL_ACCESS.value),
            "risk_score": alert_data.get("risk_score", 0),
            "priority": self._calculate_priority(alert_data.get("risk_score", 0)),
            "description": alert_data.get("description", "Suspicious activity detected"),
            "details": alert_data.get("details", {}),
            "status": "active",
            "acknowledged": False,
            "acknowledged_by": None,
            "acknowledged_at": None,
            "resolved": False,
            "resolved_by": None,
            "resolved_at": None,
            "actions_taken": []
        }
        
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        print(f"[ALERT] Alert created: {alert_id} - Priority: {alert['priority']} - User: {alert['username']}")
        
        return alert
    
    def _calculate_priority(self, risk_score: float) -> str:
        """Calculate alert priority based on risk score"""
        if risk_score >= self.alert_thresholds[AlertPriority.CRITICAL]:
            return AlertPriority.CRITICAL.value
        elif risk_score >= self.alert_thresholds[AlertPriority.HIGH]:
            return AlertPriority.HIGH.value
        elif risk_score >= self.alert_thresholds[AlertPriority.MEDIUM]:
            return AlertPriority.MEDIUM.value
        else:
            return AlertPriority.LOW.value
    
    def get_active_alerts(self, priority: Optional[str] = None) -> List[Dict]:
        """
        Get all active alerts, optionally filtered by priority
        
        Args:
            priority: Optional priority filter
            
        Returns:
            List of active alerts
        """
        if priority:
            return [alert for alert in self.active_alerts 
                   if alert["priority"] == priority and not alert["resolved"]]
        return [alert for alert in self.active_alerts if not alert["resolved"]]
    
    def get_critical_alerts(self) -> List[Dict]:
        """Get all critical priority alerts"""
        return self.get_active_alerts(priority=AlertPriority.CRITICAL.value)
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Mark an alert as acknowledged
        
        Args:
            alert_id: ID of the alert
            acknowledged_by: Username of person acknowledging
            
        Returns:
            True if successful, False otherwise
        """
        for alert in self.active_alerts:
            if alert["alert_id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_by"] = acknowledged_by
                alert["acknowledged_at"] = datetime.now().isoformat()
                print(f"[OK] Alert {alert_id} acknowledged by {acknowledged_by}")
                return True
        return False
    
    def resolve_alert(self, alert_id: str, resolved_by: str, resolution_notes: str = "") -> bool:
        """
        Mark an alert as resolved
        
        Args:
            alert_id: ID of the alert
            resolved_by: Username of person resolving
            resolution_notes: Optional notes about resolution
            
        Returns:
            True if successful, False otherwise
        """
        for alert in self.active_alerts:
            if alert["alert_id"] == alert_id:
                alert["resolved"] = True
                alert["resolved_by"] = resolved_by
                alert["resolved_at"] = datetime.now().isoformat()
                alert["resolution_notes"] = resolution_notes
                alert["status"] = "resolved"
                print(f"[OK] Alert {alert_id} resolved by {resolved_by}")
                return True
        return False
    
    def add_action(self, alert_id: str, action: str) -> bool:
        """
        Add an action taken for an alert
        
        Args:
            alert_id: ID of the alert
            action: Description of action taken
            
        Returns:
            True if successful, False otherwise
        """
        for alert in self.active_alerts:
            if alert["alert_id"] == alert_id:
                alert["actions_taken"].append({
                    "action": action,
                    "timestamp": datetime.now().isoformat()
                })
                return True
        return False
    
    def get_alert_stats(self) -> Dict:
        """
        Get statistics about alerts
        
        Returns:
            Dictionary with alert statistics
        """
        total_alerts = len(self.alert_history)
        active_count = len([a for a in self.active_alerts if not a["resolved"]])
        resolved_count = len([a for a in self.active_alerts if a["resolved"]])
        
        priority_counts = {
            "critical": len([a for a in self.active_alerts 
                           if a["priority"] == AlertPriority.CRITICAL.value and not a["resolved"]]),
            "high": len([a for a in self.active_alerts 
                        if a["priority"] == AlertPriority.HIGH.value and not a["resolved"]]),
            "medium": len([a for a in self.active_alerts 
                          if a["priority"] == AlertPriority.MEDIUM.value and not a["resolved"]]),
            "low": len([a for a in self.active_alerts 
                       if a["priority"] == AlertPriority.LOW.value and not a["resolved"]])
        }
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_count,
            "resolved_alerts": resolved_count,
            "priority_breakdown": priority_counts
        }
    
    def get_user_alerts(self, user_id: str) -> List[Dict]:
        """Get all alerts for a specific user"""
        return [alert for alert in self.alert_history if alert["user_id"] == user_id]
    
    def clear_resolved_alerts(self, days_old: int = 30) -> int:
        """
        Clear resolved alerts older than specified days
        
        Args:
            days_old: Remove alerts resolved more than this many days ago
            
        Returns:
            Number of alerts cleared
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        initial_count = len(self.active_alerts)
        self.active_alerts = [
            alert for alert in self.active_alerts
            if not alert["resolved"] or 
            datetime.fromisoformat(alert["resolved_at"]) > cutoff_date
        ]
        
        cleared_count = initial_count - len(self.active_alerts)
        
        if cleared_count > 0:
            print(f"[DEL] Cleared {cleared_count} old resolved alerts")
        
        return cleared_count

# Global instance
alert_manager = AlertManager()