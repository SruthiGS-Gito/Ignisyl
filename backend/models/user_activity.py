"""
User Activity Model
SQLAlchemy model for storing user activities
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class UserActivity(Base):
    """
    Stores user activity events for analysis
    Every user action is logged here
    """
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User information
    user_id = Column(String(100), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Activity details
    activity_type = Column(String(50), nullable=False, index=True)  # file_access, login, network_access, etc.
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Activity metadata
    description = Column(Text, nullable=True)
    source_ip = Column(String(50), nullable=True)
    destination_ip = Column(String(50), nullable=True)
    
    # File/Data information
    file_path = Column(String(500), nullable=True)
    file_size = Column(BigInteger, nullable=True)  # in bytes
    bytes_transferred = Column(BigInteger, nullable=True)  # network bytes
    
    # Location and device
    location = Column(String(100), nullable=True)
    device_info = Column(String(200), nullable=True)
    
    # Temporal information
    hour = Column(Integer, nullable=True)  # Hour of day (0-23)
    day_of_week = Column(Integer, nullable=True)  # Day of week (0-6)
    is_weekend = Column(Integer, nullable=True, default=0)  # Boolean as int
    is_business_hours = Column(Integer, nullable=True, default=1)  # Boolean as int
    
    # Risk information
    risk_score = Column(Float, nullable=True, default=0.0, index=True)
    risk_level = Column(String(20), nullable=True, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Action taken
    action = Column(String(20), nullable=True)  # ALLOW, MONITOR, RESTRICT, BLOCK
    blocked = Column(Integer, nullable=True, default=0)  # Boolean as int
    
    # Additional context (JSON stored as text)
    context_data = Column(Text, nullable=True)  # JSON string with additional context
    
    # Relationships
    user = relationship("User", back_populates="activities")
    risk_assessment = relationship("RiskAssessment", back_populates="activity", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id='{self.user_id}', type='{self.activity_type}', risk={self.risk_score})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        import json
        
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_type": self.activity_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "description": self.description,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "bytes_transferred": self.bytes_transferred,
            "location": self.location,
            "device_info": self.device_info,
            "hour": self.hour,
            "day_of_week": self.day_of_week,
            "is_weekend": bool(self.is_weekend),
            "is_business_hours": bool(self.is_business_hours),
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "action": self.action,
            "blocked": bool(self.blocked),
            "context_data": json.loads(self.context_data) if self.context_data else {}
        }
