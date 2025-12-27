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
        
        # Determine risk level - IEEE Paper Thresholds:
        # 0-30: ALLOW, 31-50: MONITOR, 51-75: RESTRICT, 76-100: BLOCK
        if current_score <= 30:
            risk_level = "LOW"
            action = "ALLOW"
            severity = "INFO"
        elif current_score <= 50:
            risk_level = "MEDIUM"
            action = "MONITOR"
            severity = "WARNING"
        elif current_score <= 75:
            risk_level = "HIGH"
            action = "RESTRICT"
            severity = "HIGH"
        else:  # current_score > 75 -> CRITICAL/BLOCK
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
            recommendations.append("[ALERT] IMMEDIATE ACTION REQUIRED")
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
            return f"[WARN] {event_name} detected (+{score_added:.1f} points). Current risk: {current_score:.1f}/100. {recent_count} suspicious events in last hour. Immediate attention required."
        else:
            return f"[ALERT] CRITICAL: {event_name} detected (+{score_added:.1f} points). Current risk: {current_score:.1f}/100. {recent_count} threat indicators in last hour. User should be blocked immediately."
    
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

    def sync_to_database(self, user_id: str, db_user_manager=None):
        """Sync intelligent engine score to database for consistency"""
        if db_user_manager is None:
            return

        profile = self.get_user_risk_profile(user_id)
        db_user_manager.update_user_activity(user_id, risk_score=profile['current_score'])

    def load_from_activities(self, user_id: str, activities: List[Dict]):
        """
        Initialize user risk profile from historical activities.
        This ensures risk scores are consistent with activity history.
        """
        if not activities:
            return

        # Reset user data
        self.user_scores[user_id] = {
            'current_score': 0,
            'events': [],
            'last_update': datetime.now(),
            'peak_score': 0
        }

        # Process activities from oldest to newest
        sorted_activities = sorted(activities, key=lambda x: x.get('timestamp', ''))

        for activity in sorted_activities:
            activity_type = activity.get('activity_type', 'unknown')
            risk_score = activity.get('risk_score', 0)

            # Update user data without time decay (historical reconstruction)
            user_data = self.user_scores[user_id]
            try:
                timestamp = datetime.fromisoformat(activity.get('timestamp', datetime.now().isoformat()))
            except:
                timestamp = datetime.now()

            # Use the ACTUAL risk score from the activity, not a mapping
            # This ensures high-risk activities (like honeypot_access with 100) are reflected
            user_data['events'].append({
                'type': activity_type,
                'score': risk_score,  # Use actual activity risk score
                'timestamp': timestamp,
                'context': {}
            })

        # Calculate final score from recent events (last 24 hours)
        user_data = self.user_scores[user_id]
        recent_events = [
            e for e in user_data['events']
            if (datetime.now() - e['timestamp']).total_seconds() < 86400  # 24 hours
        ]

        # Calculate score using weighted average with recency bias
        # Also consider the MAXIMUM risk score for recent events (for critical threats)
        if recent_events:
            # Find the maximum recent risk score
            max_recent_score = max(e['score'] for e in recent_events)

            # Calculate weighted average
            total_score = 0
            total_weight = 0
            for i, event in enumerate(sorted(recent_events, key=lambda x: x['timestamp'], reverse=True)[:20]):  # Limit to 20 most recent
                weight = 1.0 / (i + 1)  # Recency weight
                total_score += event['score'] * weight
                total_weight += weight

            weighted_avg = total_score / max(total_weight, 1)

            # Final score: weighted blend of average and maximum
            # If there's a critical threat (score > 75), weight the max more heavily
            if max_recent_score > 75:
                user_data['current_score'] = min(100, max_recent_score * 0.7 + weighted_avg * 0.3)
            else:
                user_data['current_score'] = min(100, weighted_avg * 0.6 + max_recent_score * 0.4)

        user_data['peak_score'] = max(user_data['peak_score'], user_data['current_score'])
        user_data['last_update'] = datetime.now()

# Global instance
intelligent_risk_engine = IntelligentRiskEngine()