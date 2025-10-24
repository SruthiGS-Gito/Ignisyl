"""
Risk Assessment Module for IGNISYL
Handles risk scoring and threat classification
"""

import sqlite3
import os
import sys
from datetime import datetime
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

class RiskAssessmentManager:
    """Manages risk assessments and threat classifications"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = os.path.join(settings.DATA_PATH, "ignisyl.db")
        else:
            self.db_path = db_path
    
    def create_assessment(self, user_id: int, activity_id: Optional[int],
                         risk_score: float, risk_level: str,
                         assessment_details: Dict, anomaly_factors: List[str],
                         firewall_action: str = "ALLOW") -> Optional[int]:
        """
        Create a new risk assessment
        
        Args:
            user_id: User ID
            activity_id: Associated activity ID (optional)
            risk_score: Risk score (0-100)
            risk_level: LOW, MEDIUM, HIGH
            assessment_details: Detailed assessment data
            anomaly_factors: List of risk factors detected
            firewall_action: ALLOW, RESTRICT, BLOCK
            
        Returns:
            Assessment ID or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO risk_assessments (
                        user_id, activity_id, risk_score, risk_level,
                        assessment_details, anomaly_factors, firewall_action
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    activity_id,
                    risk_score,
                    risk_level,
                    json.dumps(assessment_details),
                    json.dumps(anomaly_factors),
                    firewall_action
                ))
                
                assessment_id = cursor.lastrowid
                conn.commit()
                
                logger.debug(f"Created risk assessment {assessment_id} for user {user_id}")
                return assessment_id
                
        except Exception as e:
            logger.error(f"❌ Failed to create assessment: {e}")
            return None
    
    def get_assessment(self, assessment_id: int) -> Optional[Dict]:
        """Get risk assessment by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM risk_assessments WHERE id = ?
                """, (assessment_id,))
                
                row = cursor.fetchone()
                
                if row:
                    assessment = dict(row)
                    
                    # Parse JSON fields
                    if assessment.get('assessment_details'):
                        assessment['assessment_details'] = json.loads(assessment['assessment_details'])
                    if assessment.get('anomaly_factors'):
                        assessment['anomaly_factors'] = json.loads(assessment['anomaly_factors'])
                    
                    return assessment
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get assessment: {e}")
            return None
    
    def get_user_assessments(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get risk assessments for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM risk_assessments 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user_id, limit))
                
                assessments = []
                for row in cursor.fetchall():
                    assessment = dict(row)
                    
                    # Parse JSON fields
                    if assessment.get('assessment_details'):
                        try:
                            assessment['assessment_details'] = json.loads(assessment['assessment_details'])
                        except:
                            assessment['assessment_details'] = {}
                    
                    if assessment.get('anomaly_factors'):
                        try:
                            assessment['anomaly_factors'] = json.loads(assessment['anomaly_factors'])
                        except:
                            assessment['anomaly_factors'] = []
                    
                    assessments.append(assessment)
                
                return assessments
                
        except Exception as e:
            logger.error(f"❌ Failed to get user assessments: {e}")
            return []
    
    def get_high_risk_assessments(self, limit: int = 20, unresolved_only: bool = True) -> List[Dict]:
        """Get high-risk assessments"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if unresolved_only:
                    cursor.execute("""
                        SELECT ra.*, u.username, u.full_name, u.department
                        FROM risk_assessments ra
                        LEFT JOIN users u ON ra.user_id = u.id
                        WHERE ra.risk_level = 'HIGH' AND ra.resolved_at IS NULL
                        ORDER BY ra.created_at DESC
                        LIMIT ?
                    """, (limit,))
                else:
                    cursor.execute("""
                        SELECT ra.*, u.username, u.full_name, u.department
                        FROM risk_assessments ra
                        LEFT JOIN users u ON ra.user_id = u.id
                        WHERE ra.risk_level = 'HIGH'
                        ORDER BY ra.created_at DESC
                        LIMIT ?
                    """, (limit,))
                
                assessments = []
                for row in cursor.fetchall():
                    assessment = dict(row)
                    
                    # Parse JSON fields
                    if assessment.get('assessment_details'):
                        try:
                            assessment['assessment_details'] = json.loads(assessment['assessment_details'])
                        except:
                            pass
                    
                    if assessment.get('anomaly_factors'):
                        try:
                            assessment['anomaly_factors'] = json.loads(assessment['anomaly_factors'])
                        except:
                            pass
                    
                    assessments.append(assessment)
                
                return assessments
                
        except Exception as e:
            logger.error(f"❌ Failed to get high-risk assessments: {e}")
            return []
    
    def mark_resolved(self, assessment_id: int, is_false_positive: bool = False) -> bool:
        """Mark assessment as resolved"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE risk_assessments 
                    SET resolved_at = ?,
                        is_false_positive = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), int(is_false_positive), assessment_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"❌ Failed to mark assessment resolved: {e}")
            return False
    
    def get_assessment_stats(self, days: int = 30) -> Dict:
        """Get assessment statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                from datetime import timedelta
                date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
                
                stats = {}
                
                # Total assessments
                cursor.execute("SELECT COUNT(*) FROM risk_assessments WHERE created_at >= ?", (date_threshold,))
                stats['total_assessments'] = cursor.fetchone()[0]
                
                # By risk level
                for level in ['LOW', 'MEDIUM', 'HIGH']:
                    cursor.execute("""
                        SELECT COUNT(*) FROM risk_assessments 
                        WHERE risk_level = ? AND created_at >= ?
                    """, (level, date_threshold))
                    stats[f'{level.lower()}_risk'] = cursor.fetchone()[0]
                
                # By action
                for action in ['ALLOW', 'RESTRICT', 'BLOCK']:
                    cursor.execute("""
                        SELECT COUNT(*) FROM risk_assessments 
                        WHERE firewall_action = ? AND created_at >= ?
                    """, (action, date_threshold))
                    stats[f'action_{action.lower()}'] = cursor.fetchone()[0]
                
                # Unresolved high-risk
                cursor.execute("""
                    SELECT COUNT(*) FROM risk_assessments 
                    WHERE risk_level = 'HIGH' AND resolved_at IS NULL
                """)
                stats['unresolved_high_risk'] = cursor.fetchone()[0]
                
                # False positives
                cursor.execute("""
                    SELECT COUNT(*) FROM risk_assessments 
                    WHERE is_false_positive = 1 AND created_at >= ?
                """, (date_threshold,))
                stats['false_positives'] = cursor.fetchone()[0]
                
                # Average risk score
                cursor.execute("""
                    SELECT AVG(risk_score) FROM risk_assessments 
                    WHERE created_at >= ?
                """, (date_threshold,))
                avg = cursor.fetchone()[0]
                stats['average_risk_score'] = round(avg, 2) if avg else 0.0
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Failed to get assessment stats: {e}")
            return {}

# Global instance
try:
    risk_assessment_manager = RiskAssessmentManager()
except Exception as e:
    logger.error(f"Failed to initialize risk assessment manager: {e}")
    risk_assessment_manager = None

def main():
    """Test risk assessment functions"""
    print("\n" + "="*60)
    print("IGNISYL Risk Assessment Test")
    print("="*60 + "\n")
    
    manager = RiskAssessmentManager()
    
    # Get stats
    stats = manager.get_assessment_stats()
    print("📊 Assessment Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Get high-risk assessments
    high_risk = manager.get_high_risk_assessments(limit=5)
    print(f"\n⚠️ High-risk assessments: {len(high_risk)}")
    
    print("\n✅ Risk assessment test complete!")

if __name__ == "__main__":
    main()