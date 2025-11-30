"""
Risk Assessment Model
SQLAlchemy model for storing risk assessments
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class RiskAssessment(Base):
    """
    Stores risk assessment results for user activities
    Links to UserActivity table
    """
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Link to user activity
    activity_id = Column(Integer, ForeignKey("user_activities.id", ondelete="CASCADE"), nullable=True)
    
    # User information
    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Risk scores
    ml_risk_score = Column(Float, nullable=False, default=0.0)  # ML model prediction
    contextual_risk_score = Column(Float, nullable=False, default=0.0)  # Context-aware score
    final_risk_score = Column(Float, nullable=False, default=0.0, index=True)  # Combined score
    risk_level = Column(String(20), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Risk factors (JSON stored as text)
    triggered_factors = Column(Text, nullable=True)  # JSON list of triggered risk factors
    contextual_modifiers = Column(Text, nullable=True)  # JSON list of applied modifiers
    
    # ML model scores
    isolation_forest_score = Column(Float, nullable=True)
    autoencoder_score = Column(Float, nullable=True)
    xgboost_score = Column(Float, nullable=True)
    
    # Explanation
    risk_explanation = Column(Text, nullable=True)  # Human-readable explanation
    recommendations = Column(Text, nullable=True)  # JSON list of recommendations
    
    # Action taken
    recommended_action = Column(String(20), nullable=False)  # ALLOW, MONITOR, RESTRICT, BLOCK
    action_taken = Column(String(20), nullable=True)  # Actual action taken
    
    # Metadata
    assessed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    confidence_score = Column(Float, nullable=True)  # Model confidence (0-1)
    
    # Relationships
    user = relationship("User", back_populates="risk_assessments")
    activity = relationship("UserActivity", back_populates="risk_assessment", uselist=False)
    
    def __repr__(self):
        return f"<RiskAssessment(id={self.id}, user_id='{self.user_id}', risk_score={self.final_risk_score}, level='{self.risk_level}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        import json
        
        return {
            "id": self.id,
            "activity_id": self.activity_id,
            "user_id": self.user_id,
            "ml_risk_score": self.ml_risk_score,
            "contextual_risk_score": self.contextual_risk_score,
            "final_risk_score": self.final_risk_score,
            "risk_level": self.risk_level,
            "triggered_factors": json.loads(self.triggered_factors) if self.triggered_factors else [],
            "contextual_modifiers": json.loads(self.contextual_modifiers) if self.contextual_modifiers else [],
            "isolation_forest_score": self.isolation_forest_score,
            "autoencoder_score": self.autoencoder_score,
            "xgboost_score": self.xgboost_score,
            "risk_explanation": self.risk_explanation,
            "recommendations": json.loads(self.recommendations) if self.recommendations else [],
            "recommended_action": self.recommended_action,
            "action_taken": self.action_taken,
            "assessed_at": self.assessed_at.isoformat() if self.assessed_at else None,
            "confidence_score": self.confidence_score
        }
