"""
Advanced Risk Scoring Engine for IGNISYL
Context-aware risk assessment with business intelligence
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import sys
import os
import ipaddress
import logging
from dataclasses import dataclass

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.config import settings, RISK_LEVELS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
RARE_ACTIVITY_THRESHOLD = 0.1
TIME_DEVIATION_MULTIPLIER = 5
MAX_TIME_DEVIATION_SCORE = 30
MAX_VOLUME_DEVIATION_SCORE = 25
MAX_BASELINE_DEVIATION = 50.0
BASELINE_DEVIATION_WEIGHT = 0.5
LARGE_FILE_MULTIPLIER = 5
HIGH_TRAFFIC_MULTIPLIER = 3
BANDWIDTH_SPIKE_MULTIPLIER = 5

@dataclass
class RiskFactor:
    """Data class for risk factors"""
    name: str
    weight: float
    description: str
    category: str

@dataclass
class ContextualModifier:
    """Data class for contextual risk modifiers"""
    condition: str
    modifier: float
    description: str

class ContextualRiskScorer:
    """Advanced risk scoring with business context awareness"""
    
    def __init__(self):
        self.risk_factors = self._initialize_risk_factors()
        self.contextual_modifiers = self._initialize_contextual_modifiers()
        self.user_baselines = {}
        self.business_calendar = self._initialize_business_calendar()
        
    def _initialize_risk_factors(self) -> Dict[str, RiskFactor]:
        """Initialize risk factors with weights"""
        return {
            # Temporal Risk Factors
            'off_hours_access': RiskFactor('off_hours_access', 25.0, 'Activity outside business hours', 'temporal'),
            'weekend_activity': RiskFactor('weekend_activity', 20.0, 'Activity during weekends', 'temporal'),
            'unusual_login_time': RiskFactor('unusual_login_time', 30.0, 'Login at unusual time for user', 'temporal'),
            
            # Data Access Risk Factors
            'large_file_transfer': RiskFactor('large_file_transfer', 35.0, 'Abnormally large file transfer', 'data'),
            'sensitive_data_access': RiskFactor('sensitive_data_access', 40.0, 'Access to sensitive/classified data', 'data'),
            'cross_department_access': RiskFactor('cross_department_access', 30.0, 'Access to other department resources', 'data'),
            'mass_data_extraction': RiskFactor('mass_data_extraction', 45.0, 'Large-scale data extraction', 'data'),
            'external_data_transfer': RiskFactor('external_data_transfer', 40.0, 'Data transfer to external systems', 'data'),
            'database_mass_query': RiskFactor('database_mass_query', 35.0, 'Mass database queries', 'data'),
            
            # Network Risk Factors
            'unusual_network_traffic': RiskFactor('unusual_network_traffic', 30.0, 'Abnormal network usage patterns', 'network'),
            'external_connections': RiskFactor('external_connections', 35.0, 'Connections to external/unknown hosts', 'network'),
            'protocol_anomaly': RiskFactor('protocol_anomaly', 25.0, 'Unusual network protocols', 'network'),
            'bandwidth_spike': RiskFactor('bandwidth_spike', 30.0, 'Sudden bandwidth usage increase', 'network'),
            
            # Behavioral Risk Factors
            'login_location_change': RiskFactor('login_location_change', 40.0, 'Login from unusual location', 'behavioral'),
            'device_change': RiskFactor('device_change', 35.0, 'Login from new/unusual device', 'behavioral'),
            'session_duration_anomaly': RiskFactor('session_duration_anomaly', 25.0, 'Unusual session duration', 'behavioral'),
            'typing_pattern_change': RiskFactor('typing_pattern_change', 30.0, 'Change in typing/behavioral patterns', 'behavioral'),
            'failed_login_attempts': RiskFactor('failed_login_attempts', 45.0, 'Multiple failed login attempts', 'behavioral'),
            
            # System Risk Factors
            'privilege_escalation': RiskFactor('privilege_escalation', 50.0, 'Attempt to escalate privileges', 'system'),
            'system_file_access': RiskFactor('system_file_access', 45.0, 'Access to system/configuration files', 'system'),
            'unusual_process_execution': RiskFactor('unusual_process_execution', 40.0, 'Execution of unusual processes', 'system'),
            'log_tampering': RiskFactor('log_tampering', 60.0, 'Attempt to modify audit logs', 'system'),
            
            # Application Risk Factors
            'app_usage_anomaly': RiskFactor('app_usage_anomaly', 25.0, 'Unusual application usage patterns', 'application'),
            'unauthorized_software': RiskFactor('unauthorized_software', 35.0, 'Use of unauthorized software', 'application'),
            'suspicious_downloads': RiskFactor('suspicious_downloads', 40.0, 'Downloads of suspicious files', 'application')
        }
    
    def _initialize_contextual_modifiers(self) -> Dict[str, ContextualModifier]:
        """Initialize contextual risk modifiers"""
        return {
            # Time-based modifiers
            'month_end_finance': ContextualModifier(
                'is_month_end,department:Finance',
                -20.0,
                'Financial activities during month-end are expected'
            ),
            'quarter_end_finance': ContextualModifier(
                'is_quarter_end,department:Finance',
                -25.0,
                'Financial activities during quarter-end are expected'
            ),
            'maintenance_window_it': ContextualModifier(
                'is_maintenance_window,department:IT',
                -30.0,
                'IT activities during maintenance windows are expected'
            ),
            
            # Role-based modifiers
            'admin_high_privilege': ContextualModifier(
                'role:System Admin|Security Admin,high_privilege:true',
                -25.0,
                'High privilege activities expected for admin roles'
            ),
            'executive_travel': ContextualModifier(
                'seniority:Executive,location_change:true',
                -20.0,
                'Location changes expected for executive travel'
            ),
            'developer_code_access': ContextualModifier(
                'department:IT,code_files:true',
                -15.0,
                'Code file access expected for developers'
            ),
            
            # Business context modifiers
            'business_hours_activity': ContextualModifier(
                'is_business_hours:true',
                -5.0,
                'Activities during business hours are less suspicious'
            )
        }
    
    def _initialize_business_calendar(self) -> Dict:
        """Initialize business calendar events"""
        return {
            'month_end_days': [28, 29, 30, 31, 1, 2, 3],
            'quarter_end_months': [3, 6, 9, 12],
            'maintenance_windows': {
                'days': [6, 0],  # Saturday, Sunday
                'hours': [2, 3, 4, 5]  # 2-6 AM
            },
            'business_hours': {
                'start': 9,
                'end': 17,
                'weekdays': [0, 1, 2, 3, 4]  # Monday-Friday
            }
        }
    
    def calculate_base_risk_score(self, activity_data: Dict, user_profile: Dict) -> Tuple[float, List[str]]:
        """Calculate base risk score from detected risk factors"""
        total_score = 0.0
        triggered_factors = []
        
        # Check each risk factor
        for factor_name, factor in self.risk_factors.items():
            if self._check_risk_factor(factor_name, activity_data, user_profile):
                total_score += factor.weight
                triggered_factors.append(f"{factor.description} (+{factor.weight})")
        
        return min(total_score, 100.0), triggered_factors
    
    def _check_risk_factor(self, factor_name: str, activity_data: Dict, user_profile: Dict) -> bool:
        """Check if a specific risk factor is triggered"""
        
        # Temporal risk factors
        if factor_name == 'off_hours_access':
            hour = activity_data.get('hour', 12)
            business_hours = self.business_calendar['business_hours']
            return hour < business_hours['start'] or hour > business_hours['end']
        
        elif factor_name == 'weekend_activity':
            return activity_data.get('is_weekend', False)
        
        elif factor_name == 'unusual_login_time':
            hour = activity_data.get('hour', 12)
            user_normal_hours = user_profile.get('typical_work_hours', [9, 17])
            return hour < user_normal_hours[0] - 2 or hour > user_normal_hours[1] + 2
        
        # Data access risk factors
        elif factor_name == 'large_file_transfer':
            file_size = activity_data.get('file_size', 0)
            user_avg_size = user_profile.get('avg_file_size', 10*1024*1024)  # 10MB default
            return file_size > user_avg_size * LARGE_FILE_MULTIPLIER
        
        elif factor_name == 'sensitive_data_access':
            return activity_data.get('sensitive_data_accessed', False)
        
        elif factor_name == 'cross_department_access':
            user_dept = user_profile.get('department', '')
            accessed_resource_dept = activity_data.get('resource_department', user_dept)
            return user_dept != accessed_resource_dept and user_dept != '' and accessed_resource_dept != ''
        
        elif factor_name == 'mass_data_extraction':
            rows_affected = activity_data.get('rows_affected', 0)
            return rows_affected > 10000
        
        elif factor_name == 'external_data_transfer':
            destination = activity_data.get('destination', '')
            return 'external' in destination.lower() or 'internet' in destination.lower()
        
        # Network risk factors
        elif factor_name == 'unusual_network_traffic':
            bytes_transferred = activity_data.get('bytes_transferred', 0)
            user_avg_traffic = user_profile.get('avg_network_usage', 100*1024*1024)  # 100MB default
            return bytes_transferred > user_avg_traffic * HIGH_TRAFFIC_MULTIPLIER
        
        elif factor_name == 'external_connections':
            destination_ip = activity_data.get('destination_ip', '')
            return destination_ip and not self._is_internal_ip(destination_ip)
        
        elif factor_name == 'bandwidth_spike':
            current_bandwidth = activity_data.get('bandwidth_mbps', 0)
            user_avg_bandwidth = user_profile.get('avg_bandwidth', 10)
            return current_bandwidth > user_avg_bandwidth * BANDWIDTH_SPIKE_MULTIPLIER
        
        # Behavioral risk factors
        elif factor_name == 'login_location_change':
            current_location = activity_data.get('location', '')
            user_locations = user_profile.get('typical_locations', [])
            return current_location and current_location not in user_locations
        
        elif factor_name == 'device_change':
            current_device = activity_data.get('device_info', '')
            user_devices = user_profile.get('known_devices', [])
            return current_device and current_device not in user_devices
        
        elif factor_name == 'failed_login_attempts':
            failed_attempts = activity_data.get('failed_login_attempts', 0)
            return failed_attempts >= 3
        
        # System risk factors
        elif factor_name == 'privilege_escalation':
            return activity_data.get('privilege_escalation_attempt', False)
        
        elif factor_name == 'system_file_access':
            file_path = activity_data.get('file_path', '')
            system_paths = ['/etc/', '/sys/', '/var/log/', 'C:\\Windows\\System32\\', 'C:\\Program Files\\']
            return any(path in file_path for path in system_paths)
        
        elif factor_name == 'log_tampering':
            return activity_data.get('log_modification_attempt', False)
        
        # Application risk factors
        elif factor_name == 'unauthorized_software':
            app_name = activity_data.get('application_name', '')
            authorized_apps = user_profile.get('authorized_applications', [])
            return app_name and len(authorized_apps) > 0 and app_name not in authorized_apps
        
        elif factor_name == 'suspicious_downloads':
            file_type = activity_data.get('file_type', '')
            suspicious_types = ['.exe', '.bat', '.ps1', '.sh', '.vbs', '.cmd']
            return file_type in suspicious_types
        
        return False
    
    def _is_internal_ip(self, ip_address: str) -> bool:
        """Check if IP address is internal/private using ipaddress module"""
        if not ip_address or ip_address == 'localhost':
            return True
        
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            return ip_obj.is_private or ip_obj.is_loopback
        except ValueError:
            # Invalid IP address, treat as external for safety
            logger.warning(f"Invalid IP address: {ip_address}")
            return False
    
    def apply_contextual_modifiers(self, base_score: float, activity_data: Dict, 
                                 user_profile: Dict) -> Tuple[float, List[str]]:
        """Apply contextual modifiers to base risk score"""
        modified_score = base_score
        applied_modifiers = []
        
        for modifier_name, modifier in self.contextual_modifiers.items():
            if self._evaluate_modifier_condition(modifier.condition, activity_data, user_profile):
                modified_score += modifier.modifier
                applied_modifiers.append(f"{modifier.description} ({modifier.modifier:+.1f})")
        
        return max(0.0, min(modified_score, 100.0)), applied_modifiers
    
    def _evaluate_modifier_condition(self, condition: str, activity_data: Dict, user_profile: Dict) -> bool:
        """Evaluate contextual modifier conditions using structured format"""
        
        conditions = condition.split(',')
        all_met = True
        
        for cond in conditions:
            cond = cond.strip()
            
            # Month-end check
            if cond == 'is_month_end':
                current_day = activity_data.get('day_of_month', 15)
                if current_day not in self.business_calendar['month_end_days']:
                    all_met = False
                    break
            
            # Quarter-end check
            elif cond == 'is_quarter_end':
                current_month = activity_data.get('month', 6)
                if current_month not in self.business_calendar['quarter_end_months']:
                    all_met = False
                    break
            
            # Maintenance window check
            elif cond == 'is_maintenance_window':
                day_of_week = activity_data.get('day_of_week', 2)
                hour = activity_data.get('hour', 12)
                if not (day_of_week in self.business_calendar['maintenance_windows']['days'] or
                       hour in self.business_calendar['maintenance_windows']['hours']):
                    all_met = False
                    break
            
            # Business hours check
            elif cond == 'is_business_hours:true':
                hour = activity_data.get('hour', 12)
                day_of_week = activity_data.get('day_of_week', 2)
                bh = self.business_calendar['business_hours']
                if not (bh['start'] <= hour <= bh['end'] and day_of_week in bh['weekdays']):
                    all_met = False
                    break
            
            # Department checks
            elif cond.startswith('department:'):
                expected_dept = cond.split(':')[1]
                user_dept = user_profile.get('department', '')
                if user_dept != expected_dept:
                    all_met = False
                    break
            
            # Role checks
            elif cond.startswith('role:'):
                expected_roles = cond.split(':')[1].split('|')
                user_role = user_profile.get('role', '')
                if user_role not in expected_roles:
                    all_met = False
                    break
            
            # Seniority checks
            elif cond.startswith('seniority:'):
                expected_seniority = cond.split(':')[1]
                seniority = user_profile.get('seniority_level', '')
                if seniority != expected_seniority:
                    all_met = False
                    break
            
            # High privilege check
            elif cond.startswith('high_privilege:'):
                expected = cond.split(':')[1] == 'true'
                has_privilege = activity_data.get('requires_high_privilege', False)
                if has_privilege != expected:
                    all_met = False
                    break
        
        return all_met
    
    def calculate_behavioral_baseline_deviation(self, activity_data: Dict, user_profile: Dict) -> float:
        """Calculate how much the activity deviates from user's behavioral baseline"""
        
        deviation_score = 0.0
        
        # Time-based deviation
        hour = activity_data.get('hour', 12)
        typical_hours = user_profile.get('typical_work_hours', [9, 17])
        
        if hour < typical_hours[0] or hour > typical_hours[1]:
            time_deviation = min(abs(hour - typical_hours[0]), abs(hour - typical_hours[1]))
            deviation_score += min(time_deviation * TIME_DEVIATION_MULTIPLIER, MAX_TIME_DEVIATION_SCORE)
        
        # Activity frequency deviation
        activity_type = activity_data.get('activity_type', '')
        user_activity_freq = user_profile.get('activity_frequencies', {})
        typical_freq = user_activity_freq.get(activity_type, 0.5)
        
        if typical_freq < RARE_ACTIVITY_THRESHOLD:  # Rare activity for this user
            deviation_score += 20
        
        # Data volume deviation
        data_volume = activity_data.get('file_size', 0) + activity_data.get('bytes_transferred', 0)
        typical_volume = user_profile.get('typical_data_volume', 10*1024*1024)
        
        if typical_volume > 0 and data_volume > typical_volume * 3:
            volume_ratio = min(data_volume / (typical_volume + 1e-8), 10)
            deviation_score += min(volume_ratio * 5, MAX_VOLUME_DEVIATION_SCORE)
        
        return min(deviation_score, MAX_BASELINE_DEVIATION)
    
    def generate_risk_explanation(self, risk_score: float, triggered_factors: List[str], 
                                applied_modifiers: List[str], baseline_deviation: float) -> Dict:
        """Generate detailed explanation of risk assessment"""
        
        risk_level = self._determine_risk_level(risk_score)
        
        explanation = {
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'baseline_deviation': round(baseline_deviation, 2),
            'triggered_factors': triggered_factors,
            'applied_modifiers': applied_modifiers,
            'summary': self._generate_risk_summary(risk_score, risk_level, triggered_factors),
            'recommendations': self._generate_recommendations(risk_level, triggered_factors)
        }
        
        return explanation
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        low_threshold = getattr(settings, 'LOW_RISK_THRESHOLD', 30)
        medium_threshold = getattr(settings, 'MEDIUM_RISK_THRESHOLD', 70)
        
        if risk_score < low_threshold:
            return "LOW"
        elif risk_score < medium_threshold:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _generate_risk_summary(self, risk_score: float, risk_level: str, triggered_factors: List[str]) -> str:
        """Generate human-readable risk summary"""
        
        if risk_level == "LOW":
            summary = f"Activity appears normal with minimal risk indicators (Score: {risk_score:.1f})"
        elif risk_level == "MEDIUM":
            num_factors = len(triggered_factors)
            summary = f"Moderate risk detected with {num_factors} concerning factor{'s' if num_factors != 1 else ''} (Score: {risk_score:.1f})"
        else:
            summary = f"High risk activity detected with multiple threat indicators (Score: {risk_score:.1f})"
        
        if triggered_factors:
            # Show top 3 concerns
            top_concerns = [f.split(' (+')[0] for f in triggered_factors[:3]]
            summary += f". Primary concerns: {', '.join(top_concerns)}"
        
        return summary
    
    def _generate_recommendations(self, risk_level: str, triggered_factors: List[str]) -> List[str]:
        """Generate actionable recommendations based on risk assessment"""
        
        recommendations = []
        
        if risk_level == "LOW":
            recommendations.append("Continue normal monitoring")
            recommendations.append("No immediate action required")
        
        elif risk_level == "MEDIUM":
            recommendations.append("Increase monitoring frequency for this user")
            recommendations.append("Review activity details for business justification")
            recommendations.append("Consider temporary access restrictions if pattern continues")
        
        else:  # HIGH risk
            recommendations.append("Immediate investigation required")
            recommendations.append("Consider isolating user access pending review")
            recommendations.append("Alert security team and management")
            recommendations.append("Preserve logs and evidence for potential incident response")
        
        # Extract risk factor categories
        triggered_factor_names = set()
        for factor_text in triggered_factors:
            for factor_name, factor_obj in self.risk_factors.items():
                if factor_obj.description in factor_text:
                    triggered_factor_names.add(factor_name)
        
        # Add specific recommendations based on actual triggered factor names
        if any('external' in name for name in triggered_factor_names):
            recommendations.append("Review and validate all external data transfers")
        
        if any('privilege' in name for name in triggered_factor_names):
            recommendations.append("Audit user permissions and access rights")
        
        if any('time' in name or 'hours' in name for name in triggered_factor_names):
            recommendations.append("Verify business justification for off-hours activity")
        
        if any('login' in name for name in triggered_factor_names):
            recommendations.append("Verify user identity and investigate potential account compromise")
        
        return recommendations
    
    def assess_activity_risk(self, activity_data: Dict, user_profile: Dict) -> Dict:
        """Main method to assess risk for a single activity"""
        
        # Calculate base risk score
        base_score, triggered_factors = self.calculate_base_risk_score(activity_data, user_profile)
        
        # Apply contextual modifiers
        contextual_score, applied_modifiers = self.apply_contextual_modifiers(
            base_score, activity_data, user_profile
        )
        
        # Calculate behavioral baseline deviation
        baseline_deviation = self.calculate_behavioral_baseline_deviation(activity_data, user_profile)
        
        # Final risk score combines contextual score and baseline deviation
        final_score = min(contextual_score + (baseline_deviation * BASELINE_DEVIATION_WEIGHT), 100.0)
        
        # Generate comprehensive explanation
        explanation = self.generate_risk_explanation(
            final_score, triggered_factors, applied_modifiers, baseline_deviation
        )
        
        return explanation

def test_risk_scorer():
    """Test the contextual risk scorer"""
    logger.info("="*60)
    logger.info("Testing Contextual Risk Scorer")
    logger.info("="*60)
    
    scorer = ContextualRiskScorer()
    
    # Test case 1: Normal business activity
    normal_activity = {
        'hour': 10,
        'day_of_week': 2,  # Wednesday
        'is_weekend': False,
        'activity_type': 'file_access',
        'file_size': 1024*1024,  # 1MB
        'destination': 'internal_server'
    }
    
    normal_user = {
        'department': 'Finance',
        'role': 'Financial Analyst',
        'typical_work_hours': [9, 17],
        'avg_file_size': 2*1024*1024,
        'activity_frequencies': {'file_access': 0.8}
    }
    
    result1 = scorer.assess_activity_risk(normal_activity, normal_user)
    logger.info(f"\n📊 Normal Activity:")
    logger.info(f"   Risk Level: {result1['risk_level']}, Score: {result1['risk_score']:.1f}")
    logger.info(f"   Summary: {result1['summary']}")
    
    # Test case 2: Suspicious after-hours activity
    suspicious_activity = {
        'hour': 2,  # 2 AM
        'day_of_week': 6,  # Sunday
        'is_weekend': True,
        'activity_type': 'database_query',
        'rows_affected': 50000,
        'destination': 'external_server',
        'file_size': 100*1024*1024,  # 100MB
        'sensitive_data_accessed': True
    }
    
    suspicious_user = {
        'department': 'HR',
        'role': 'HR Coordinator',
        'typical_work_hours': [9, 17],
        'avg_file_size': 1*1024*1024,
        'activity_frequencies': {'database_query': 0.1}
    }
    
    result2 = scorer.assess_activity_risk(suspicious_activity, suspicious_user)
    logger.info(f"\n⚠️ Suspicious Activity:")
    logger.info(f"   Risk Level: {result2['risk_level']}, Score: {result2['risk_score']:.1f}")
    logger.info(f"   Summary: {result2['summary']}")
    logger.info(f"   Recommendations: {result2['recommendations'][:2]}")
    
    # Test case 3: Month-end finance activity (should have reduced risk)
    monthend_activity = {
        'hour': 20,  # 8 PM
        'day_of_week': 4,  # Friday
        'day_of_month': 31,  # Month end
        'is_weekend': False,
        'activity_type': 'file_download',
        'file_size': 50*1024*1024,  # 50MB
        'destination': 'internal_server'
    }
    
    finance_user = {
        'department': 'Finance',
        'role': 'Financial Controller',
        'typical_work_hours': [8, 18],
        'avg_file_size': 10*1024*1024,
        'activity_frequencies': {'file_download': 0.6}
    }
    
    result3 = scorer.assess_activity_risk(monthend_activity, finance_user)
    logger.info(f"\n📈 Month-end Finance Activity:")
    logger.info(f"   Risk Level: {result3['risk_level']}, Score: {result3['risk_score']:.1f}")
    logger.info(f"   Summary: {result3['summary']}")
    if result3['applied_modifiers']:
        logger.info(f"   Applied Modifiers: {result3['applied_modifiers'][:2]}")
    
    logger.info("\n✅ Risk scorer testing completed!")
    
    return scorer

if __name__ == "__main__":
    test_risk_scorer()