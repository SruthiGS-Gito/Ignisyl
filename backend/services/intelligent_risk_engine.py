"""
Intelligent Risk Scoring Engine
Implements progressive, context-aware risk assessment
"""

from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

class IntelligentRiskEngine:
    """
    Smart risk scoring with:
    - Progressive accumulation
    - Time decay
    - Pattern detection
    - Context awareness
    """
    
    def __init__(self):
        # Store user risk history
        self.user_scores = defaultdict(lambda: {
            'current_score': 0,
            'events': [],
            'last_update': datetime.now(),
            'peak_score': 0
        })
        
        # Risk event scoring matrix
        self.event_scores = {
            # High severity - instant investigation
            'honeypot_access': 50,          # Very suspicious
            'mass_data_download': 40,        # Data exfiltration attempt
            'privilege_escalation': 45,      # Trying to gain admin access
            
            # Medium severity - monitor closely
            'large_file_transfer': 25,       # Could be legitimate or suspicious
            'after_hours_access': 20,        # Working late or suspicious?
            'unusual_location': 30,          # VPN or actual breach?
            'failed_login_attempts': 15,     # Per attempt
            'usb_device_connection': 20,     # Could be legitimate
            
            # Low severity - note but don't panic
            'sensitive_file_access': 15,     # Might be authorized
            'external_email': 10,            # Common in business
            'unusual_application': 12,       # Might be new tool
        }
        
        # Multipliers for patterns
        self.pattern_multipliers = {
            'rapid_succession': 1.5,     # Multiple events in 5 minutes
            'after_hours': 1.3,          # Between 10 PM - 6 AM
            'weekend': 1.2,              # Saturday or Sunday
            'multiple_types': 1.4        # Different threat types
        }
        
        # Time decay settings
        self.decay_rate = 5  # Points decay per hour of good behavior
        self.decay_threshold = 24  # Hours before significant decay
    
    def assess_event(self, user_id: str, event_type: str, 
                    context: Dict = None) -> Dict:
        """
        Assess a security event with intelligent scoring
        
        Args:
            user_id: User identifier
            event_type: Type of event (e.g., 'honeypot_access')
            context: Additional context (time, location, etc.)
            
        Returns:
            Assessment with updated risk score and recommendations
        """
        if context is None:
            context = {}
        
        # Apply time decay first
        self._apply_time_decay(user_id)
        
        # Get base score for this event
        base_score = self.event_scores.get(event_type, 10)
        
        # Apply contextual multipliers
        final_score = self._apply_multipliers(
            user_id, event_type, base_score, context
        )
        
        # Update user's risk profile
        user_data = self.user_scores[user_id]
        user_data['events'].append({
            'type': event_type,
            'score': final_score,
            'timestamp': datetime.now(),
            'context': context
        })
        
        # Calculate new total score
        user_data['current_score'] = min(
            user_data['current_score'] + final_score,
            100  # Cap at 100
        )
        
        user_data['peak_score'] = max(
            user_data['peak_score'],
            user_data['current_score']
        )
        
        user_data['last_update'] = datetime.now()
        
        # Determine risk level and actions
        return self._generate_assessment(user_id, event_type, final_score)
    
    def _apply_time_decay(self, user_id: str):
        """Apply time-based score decay"""
        user_data = self.user_scores[user_id]
        
        hours_since_update = (
            datetime.now() - user_data['last_update']
        ).total_seconds() / 3600
        
        if hours_since_update >= 1:
            # Decay score for good behavior
            decay_amount = int(hours_since_update) * self.decay_rate
            user_data['current_score'] = max(
                0,
                user_data['current_score'] - decay_amount
            )
    
    def _apply_multipliers(self, user_id: str, event_type: str,
                          base_score: float, context: Dict) -> float:
        """Apply contextual multipliers"""
        multiplier = 1.0
        
        user_data = self.user_scores[user_id]
        
        # Check for rapid succession (multiple events in 5 minutes)
        recent_events = [
            e for e in user_data['events']
            if (datetime.now() - e['timestamp']).total_seconds() < 300
        ]
        
        if len(recent_events) >= 2:
            multiplier *= self.pattern_multipliers['rapid_succession']
        
        # Check time of day
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            multiplier *= self.pattern_multipliers['after_hours']
        
        # Check day of week
        if datetime.now().weekday() >= 5:  # Saturday or Sunday
            multiplier *= self.pattern_multipliers['weekend']
        
        # Check for multiple threat types
        event_types = set(e['type'] for e in recent_events)
        if len(event_types) >= 3:
            multiplier *= self.pattern_multipliers['multiple_types']
        
        return base_score * multiplier
    
    def _generate_assessment(self, user_id: str, event_type: str,
                            score_added: float) -> Dict:
        """Generate risk assessment and recommendations"""
        user_data = self.user_scores[user_id]
        current_score = user_data['current_score']
        
        # Determine risk level
        if current_score < 30:
            risk_level = "LOW"
            action = "ALLOW"
            severity = "INFO"
        elif current_score < 50:
            risk_level = "MEDIUM"
            action = "MONITOR"
            severity = "WARNING"
        elif current_score < 75:
            risk_level = "HIGH"
            action = "RESTRICT"
            severity = "HIGH"
        else:
            risk_level = "CRITICAL"
            action = "BLOCK"
            severity = "CRITICAL"
        
        # Generate recommendations
        recommendations = self._get_recommendations(
            risk_level, event_type, user_data
        )
        
        # Create summary
        summary = self._create_summary(
            event_type, score_added, current_score, user_data
        )
        
        return {
            'user_id': user_id,
            'event_type': event_type,
            'score_added': round(score_added, 1),
            'current_score': round(current_score, 1),
            'peak_score': round(user_data['peak_score'], 1),
            'risk_level': risk_level,
            'recommended_action': action,
            'severity': severity,
            'summary': summary,
            'recommendations': recommendations,
            'recent_events_count': len([
                e for e in user_data['events']
                if (datetime.now() - e['timestamp']).total_seconds() < 3600
            ])
        }
    
    def _get_recommendations(self, risk_level: str, event_type: str,
                            user_data: Dict) -> List[str]:
        """Generate contextual recommendations"""
        recommendations = []
        
        if risk_level == "LOW":
            recommendations.append("Continue standard monitoring")
        
        elif risk_level == "MEDIUM":
            recommendations.append("Increase monitoring frequency")
            recommendations.append("Review user's recent activities")
            if event_type == 'honeypot_access':
                recommendations.append("Interview user about file access")
        
        elif risk_level == "HIGH":
            recommendations.append("Alert security team immediately")
            recommendations.append("Restrict access to sensitive resources")
            recommendations.append("Enable detailed activity logging")
            recommendations.append("Consider temporary account suspension")
        
        else:  # CRITICAL
            recommendations.append("🚨 IMMEDIATE ACTION REQUIRED")
            recommendations.append("Block user access immediately")
            recommendations.append("Preserve all logs for investigation")
            recommendations.append("Notify management and legal")
            recommendations.append("Begin incident response protocol")
        
        return recommendations
    
    def _create_summary(self, event_type: str, score_added: float,
                       current_score: float, user_data: Dict) -> str:
        """Create human-readable summary"""
        event_names = {
            'honeypot_access': 'Honeypot file access',
            'large_file_transfer': 'Large file transfer',
            'after_hours_access': 'After-hours system access',
            'failed_login_attempts': 'Failed login attempt',
            'usb_device_connection': 'USB device connection'
        }
        
        event_name = event_names.get(event_type, event_type.replace('_', ' '))
        
        recent_count = len([
            e for e in user_data['events']
            if (datetime.now() - e['timestamp']).total_seconds() < 3600
        ])
        
        if current_score < 30:
            return f"{event_name} detected (+{score_added:.1f} points). Current risk: {current_score:.1f}/100. Normal activity pattern."
        elif current_score < 50:
            return f"{event_name} detected (+{score_added:.1f} points). Current risk: {current_score:.1f}/100. {recent_count} events in last hour. Monitoring recommended."
        elif current_score < 75:
            return f"⚠️ {event_name} detected (+{score_added:.1f} points). Current risk: {current_score:.1f}/100. {recent_count} suspicious events in last hour. Immediate attention required."
        else:
            return f"🚨 CRITICAL: {event_name} detected (+{score_added:.1f} points). Current risk: {current_score:.1f}/100. {recent_count} threat indicators in last hour. User should be blocked immediately."
    
    def get_user_risk_profile(self, user_id: str) -> Dict:
        """Get complete risk profile for a user"""
        self._apply_time_decay(user_id)
        user_data = self.user_scores[user_id]
        
        return {
            'user_id': user_id,
            'current_score': round(user_data['current_score'], 1),
            'peak_score': round(user_data['peak_score'], 1),
            'total_events': len(user_data['events']),
            'recent_events': len([
                e for e in user_data['events']
                if (datetime.now() - e['timestamp']).total_seconds() < 3600
            ]),
            'last_activity': user_data['last_update'].isoformat() if user_data['events'] else None
        }

# Global instance
intelligent_risk_engine = IntelligentRiskEngine()