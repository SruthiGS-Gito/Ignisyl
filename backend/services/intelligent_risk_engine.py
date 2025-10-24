"""
Intelligent Risk Scoring Engine for IGNISYL
Implements progressive, context-aware risk assessment with time decay
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from config.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentRiskEngine:
    """
    Smart risk scoring with:
    - Progressive accumulation (scores add up)
    - Time decay (good behavior reduces score)
    - Pattern detection (multiple events = higher risk)
    - Context awareness (time of day, day of week)
    """
    
    def __init__(self):
        # Store user risk history (in-memory for now)
        self.user_scores = defaultdict(lambda: {
            'current_score': 0,
            'events': [],
            'last_update': datetime.now(),
            'peak_score': 0,
            'created_at': datetime.now()
        })
        
        # Risk event scoring matrix (base scores)
        self.event_scores = {
            # CRITICAL SEVERITY - Instant investigation
            'honeypot_access': 50,          # Accessing decoy files
            'mass_data_download': 45,       # Data exfiltration attempt
            'privilege_escalation': 45,     # Trying to gain admin access
            'malware_detected': 50,         # Malware found
            
            # HIGH SEVERITY - Monitor closely
            'large_file_transfer': 30,      # >100MB transfer
            'after_hours_access': 25,       # Outside 6 AM - 10 PM
            'unusual_location': 30,         # New location/IP
            'sensitive_file_access': 25,    # Accessing confidential data
            'usb_device_connection': 25,    # USB device inserted
            
            # MEDIUM SEVERITY - Note and track
            'failed_login_attempts': 15,    # Per failed attempt
            'external_email': 12,           # Email to external domain
            'database_query': 20,           # Database access
            'file_download': 15,            # Regular file download
            
            # LOW SEVERITY - Standard monitoring
            'login': 5,                     # Normal login
            'file_access': 8,               # Normal file access
            'network_access': 8,            # Network activity
            'application_launch': 5,        # App usage
            'unknown_activity': 10          # Unclassified
        }
        
        # Multipliers for patterns
        self.pattern_multipliers = {
            'rapid_succession': 1.5,     # Multiple events in 5 minutes
            'after_hours': 1.3,          # Between 10 PM - 6 AM
            'weekend': 1.2,              # Saturday or Sunday
            'multiple_types': 1.4,       # Different threat types
            'high_volume': 1.3           # Many events in short time
        }
        
        # Time decay settings
        self.decay_rate = 5              # Points decay per hour of good behavior
        self.decay_threshold = 1         # Hours before decay starts
        self.max_score = 100             # Maximum risk score
        
        logger.info("🧠 Intelligent Risk Engine initialized")
    
    def assess_event(self, user_id: str, event_type: str, 
                    context: Dict = None) -> Dict:
        """
        Assess a security event with intelligent scoring
        
        Args:
            user_id: User identifier
            event_type: Type of event (e.g., 'honeypot_access')
            context: Additional context (time, location, bytes, etc.)
            
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
            'base_score': base_score,
            'final_score': final_score,
            'timestamp': datetime.now(),
            'context': context
        })
        
        # Calculate new total score (cap at max_score)
        previous_score = user_data['current_score']
        user_data['current_score'] = min(
            user_data['current_score'] + final_score,
            self.max_score
        )
        
        # Track peak score
        user_data['peak_score'] = max(
            user_data['peak_score'],
            user_data['current_score']
        )
        
        user_data['last_update'] = datetime.now()
        
        # Clean up old events (keep last 1000)
        if len(user_data['events']) > 1000:
            user_data['events'] = user_data['events'][-1000:]
        
        # Generate assessment
        assessment = self._generate_assessment(user_id, event_type, final_score)
        
        # Log significant events
        if assessment['risk_level'] in ['HIGH', 'CRITICAL']:
            logger.warning(
                f"⚠️ {assessment['risk_level']} risk for user {user_id}: "
                f"{event_type} (+{final_score:.1f} pts, total: {user_data['current_score']:.1f})"
            )
        
        return assessment
    
    def _apply_time_decay(self, user_id: str):
        """Apply time-based score decay for good behavior"""
        user_data = self.user_scores[user_id]
        
        hours_since_update = (
            datetime.now() - user_data['last_update']
        ).total_seconds() / 3600
        
        if hours_since_update >= self.decay_threshold:
            # Decay score for good behavior
            decay_amount = int(hours_since_update) * self.decay_rate
            
            if decay_amount > 0:
                old_score = user_data['current_score']
                user_data['current_score'] = max(
                    0,
                    user_data['current_score'] - decay_amount
                )
                
                if old_score > 0 and user_data['current_score'] < old_score:
                    logger.debug(
                        f"⏰ Score decay for user {user_id}: "
                        f"{old_score:.1f} → {user_data['current_score']:.1f} "
                        f"(-{decay_amount} pts after {hours_since_update:.1f}h)"
                    )
    
    def _apply_multipliers(self, user_id: str, event_type: str,
                          base_score: float, context: Dict) -> float:
        """Apply contextual multipliers to base score"""
        multiplier = 1.0
        applied_multipliers = []
        
        user_data = self.user_scores[user_id]
        
        # Check for rapid succession (multiple events in 5 minutes)
        recent_events = [
            e for e in user_data['events']
            if (datetime.now() - e['timestamp']).total_seconds() < 300
        ]
        
        if len(recent_events) >= 3:
            multiplier *= self.pattern_multipliers['rapid_succession']
            applied_multipliers.append('rapid_succession')
        
        # Check time of day
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            multiplier *= self.pattern_multipliers['after_hours']
            applied_multipliers.append('after_hours')
        
        # Check day of week
        if datetime.now().weekday() >= 5:  # Saturday or Sunday
            multiplier *= self.pattern_multipliers['weekend']
            applied_multipliers.append('weekend')
        
        # Check for multiple threat types
        event_types_recent = set(e['type'] for e in recent_events)
        if len(event_types_recent) >= 3:
            multiplier *= self.pattern_multipliers['multiple_types']
            applied_multipliers.append('multiple_types')
        
        # Check for high volume (many events in last hour)
        events_last_hour = [
            e for e in user_data['events']
            if (datetime.now() - e['timestamp']).total_seconds() < 3600
        ]
        if len(events_last_hour) >= 10:
            multiplier *= self.pattern_multipliers['high_volume']
            applied_multipliers.append('high_volume')
        
        # Log significant multipliers
        if multiplier > 1.2:
            logger.debug(
                f"📈 Multipliers for {user_id}: {applied_multipliers} "
                f"(×{multiplier:.2f})"
            )
        
        return base_score * multiplier
    
    def _generate_assessment(self, user_id: str, event_type: str,
                            score_added: float) -> Dict:
        """Generate risk assessment and recommendations"""
        user_data = self.user_scores[user_id]
        current_score = user_data['current_score']
        
        # Determine risk level and action
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
        
        # Count recent events
        recent_events_1h = len([
            e for e in user_data['events']
            if (datetime.now() - e['timestamp']).total_seconds() < 3600
        ])
        
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
            'recent_events_count': recent_events_1h,
            'total_events': len(user_data['events']),
            'assessment_timestamp': datetime.now().isoformat()
        }
    
    def _get_recommendations(self, risk_level: str, event_type: str,
                            user_data: Dict) -> List[str]:
        """Generate contextual recommendations"""
        recommendations = []
        
        if risk_level == "LOW":
            recommendations.append("✅ Continue standard monitoring")
            recommendations.append("No action required at this time")
        
        elif risk_level == "MEDIUM":
            recommendations.append("⚠️ Increase monitoring frequency")
            recommendations.append("Review user's recent activities")
            recommendations.append("Check for unusual patterns")
            
            if event_type == 'honeypot_access':
                recommendations.append("🚨 Interview user about honeypot file access")
            elif event_type == 'large_file_transfer':
                recommendations.append("Verify legitimacy of large file transfer")
        
        elif risk_level == "HIGH":
            recommendations.append("🚨 Alert security team immediately")
            recommendations.append("Restrict access to sensitive resources")
            recommendations.append("Enable detailed activity logging")
            recommendations.append("Consider temporary account restrictions")
            recommendations.append("Schedule security interview with user")
        
        else:  # CRITICAL
            recommendations.append("🚨🚨 IMMEDIATE ACTION REQUIRED")
            recommendations.append("Block user access immediately")
            recommendations.append("Preserve all logs for investigation")
            recommendations.append("Notify management and security team")
            recommendations.append("Begin incident response protocol")
            recommendations.append("Consider involving law enforcement")
        
        return recommendations
    
    def _create_summary(self, event_type: str, score_added: float,
                       current_score: float, user_data: Dict) -> str:
        """Create human-readable summary"""
        event_names = {
            'honeypot_access': 'Honeypot file access',
            'large_file_transfer': 'Large file transfer',
            'after_hours_access': 'After-hours system access',
            'failed_login_attempts': 'Failed login attempt',
            'usb_device_connection': 'USB device connection',
            'sensitive_file_access': 'Sensitive file access',
            'database_query': 'Database query',
            'privilege_escalation': 'Privilege escalation attempt',
            'mass_data_download': 'Mass data download',
            'malware_detected': 'Malware detected'
        }
        
        event_name = event_names.get(event_type, event_type.replace('_', ' ').title())
        
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
        
        # Get event type breakdown
        event_types = {}
        for event in user_data['events']:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Get recent events (last hour)
        recent_events = [
            e for e in user_data['events']
            if (datetime.now() - e['timestamp']).total_seconds() < 3600
        ]
        
        return {
            'user_id': user_id,
            'current_score': round(user_data['current_score'], 1),
            'peak_score': round(user_data['peak_score'], 1),
            'total_events': len(user_data['events']),
            'recent_events': len(recent_events),
            'event_type_breakdown': event_types,
            'last_activity': user_data['last_update'].isoformat() if user_data['events'] else None,
            'created_at': user_data['created_at'].isoformat()
        }
    
    def get_all_users_summary(self) -> List[Dict]:
        """Get summary of all monitored users"""
        summaries = []
        
        for user_id, user_data in self.user_scores.items():
            self._apply_time_decay(user_id)
            
            summaries.append({
                'user_id': user_id,
                'current_score': round(user_data['current_score'], 1),
                'peak_score': round(user_data['peak_score'], 1),
                'total_events': len(user_data['events']),
                'last_activity': user_data['last_update'].isoformat()
            })
        
        # Sort by current score (highest first)
        summaries.sort(key=lambda x: x['current_score'], reverse=True)
        
        return summaries
    
    def reset_user_score(self, user_id: str) -> bool:
        """Reset a user's risk score (e.g., after investigation)"""
        if user_id in self.user_scores:
            self.user_scores[user_id]['current_score'] = 0
            logger.info(f"🔄 Reset risk score for user {user_id}")
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get engine statistics"""
        return {
            'total_users_monitored': len(self.user_scores),
            'total_events': sum(len(u['events']) for u in self.user_scores.values()),
            'high_risk_users': len([
                u for u in self.user_scores.values()
                if u['current_score'] >= 50
            ]),
            'critical_risk_users': len([
                u for u in self.user_scores.values()
                if u['current_score'] >= 75
            ])
        }

# Global instance
try:
    intelligent_risk_engine = IntelligentRiskEngine()
except Exception as e:
    logger.error(f"Failed to initialize intelligent risk engine: {e}")
    intelligent_risk_engine = None

def main():
    """Test intelligent risk engine"""
    print("\n" + "="*60)
    print("IGNISYL Intelligent Risk Engine Test")
    print("="*60 + "\n")
    
    engine = IntelligentRiskEngine()
    
    # Test different events
    print("Testing event assessments...")
    
    # Low risk event
    result = engine.assess_event("test_user_1", "login", {"ip": "192.168.1.100"})
    print(f"\n1. Login event: Risk {result['current_score']}/100 ({result['risk_level']})")
    
    # Medium risk event
    result = engine.assess_event("test_user_1", "large_file_transfer", {"bytes": 150000000})
    print(f"2. Large transfer: Risk {result['current_score']}/100 ({result['risk_level']})")
    
    # High risk event
    result = engine.assess_event("test_user_1", "honeypot_access", {})
    print(f"3. Honeypot access: Risk {result['current_score']}/100 ({result['risk_level']})")
    print(f"   Summary: {result['summary']}")
    
    # Get user profile
    profile = engine.get_user_risk_profile("test_user_1")
    print(f"\n📊 User Profile:")
    for key, value in profile.items():
        print(f"   {key}: {value}")
    
    # Get stats
    stats = engine.get_stats()
    print(f"\n📈 Engine Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Intelligent risk engine test complete!")

if __name__ == "__main__":
    main()