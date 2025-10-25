"""
Database Models and Setup for IGNISYL
SQLAlchemy ORM models for user activities, risk assessments, and system logs
"""
# This file : Defines the database structure using SQLAlchemy
# - Creates tables for users, activities, risk assessments, alerts
# - Establishes relationships between different data entities
# - Provides functions to initialize database with sample data

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.config import get_database_url, ensure_directories

# Create database engine
engine = create_engine(get_database_url(), echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    """User model for tracking employees/users in the system"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    full_name = Column(String(100))
    department = Column(String(50))
    role = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    activities = relationship("UserActivity", back_populates="user")
    risk_assessments = relationship("RiskAssessment", back_populates="user")

class UserActivity(Base):
    """Model for tracking user activities and behaviors"""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # login, file_access, etc.
    activity_details = Column(Text)  # JSON string with activity details
    source_ip = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))
    device_info = Column(String(200))
    file_path = Column(String(500))  # For file operations
    file_size = Column(Integer)  # File size in bytes
    network_bytes = Column(Integer)  # Network traffic in bytes
    protocol = Column(String(20))  # HTTP, FTP, SSH, etc.
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_suspicious = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)  # ML model confidence
    
    # Relationships
    user = relationship("User", back_populates="activities")

class RiskAssessment(Base):
    """Model for storing risk assessment results"""
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0-100 risk score
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH
    assessment_details = Column(Text)  # JSON with detailed analysis
    anomaly_factors = Column(Text)  # What made this risky
    firewall_action = Column(String(20))  # ALLOW, RESTRICT, BLOCK
    is_false_positive = Column(Boolean, default=None)  # Admin feedback
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="risk_assessments")

class FirewallRule(Base):
    """Model for tracking dynamic firewall rules"""
    __tablename__ = "firewall_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    rule_type = Column(String(20), nullable=False)  # ALLOW, BLOCK, RESTRICT
    source_ip = Column(String(45))
    destination_ip = Column(String(45))
    port = Column(Integer)
    protocol = Column(String(20))
    rule_details = Column(Text)  # Additional rule parameters
    is_active = Column(Boolean, default=True)
    created_by = Column(String(50))  # System or admin username
    expires_at = Column(DateTime(timezone=True))  # Auto-expire rules
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Alert(Base):
    """Model for security alerts and notifications"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    alert_type = Column(String(50), nullable=False)  # INSIDER_THREAT, ANOMALY, etc.
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    title = Column(String(200), nullable=False)
    description = Column(Text)
    alert_data = Column(Text)  # JSON with detailed alert information
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(50))
    acknowledged_at = Column(DateTime(timezone=True))
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(50))
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemLog(Base):
    """Model for system-level logging and audit trail"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    component = Column(String(50), nullable=False)  # ML_ENGINE, FIREWALL, API, etc.
    event_type = Column(String(50))
    message = Column(Text, nullable=False)
    additional_data = Column(Text)  # JSON with extra context
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MLModelMetrics(Base):
    """Model for tracking ML model performance and metrics"""
    __tablename__ = "ml_model_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(20))
    metric_name = Column(String(50), nullable=False)  # accuracy, precision, recall, etc.
    metric_value = Column(Float, nullable=False)
    training_data_size = Column(Integer)
    evaluation_date = Column(DateTime(timezone=True), server_default=func.now())
    additional_metrics = Column(Text)  # JSON with detailed metrics

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    ensure_directories()
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def init_sample_data():
    """Initialize database with sample data for demonstration"""
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(User).count() > 0:
            print("📊 Sample data already exists")
            return
        
        # Create sample users
        sample_users = [
            User(
                username="john.doe",
                email="john.doe@company.com",
                full_name="John Doe",
                department="IT",
                role="Software Engineer"
            ),
            User(
                username="jane.smith",
                email="jane.smith@company.com", 
                full_name="Jane Smith",
                department="Finance",
                role="Financial Analyst"
            ),
            User(
                username="mike.wilson",
                email="mike.wilson@company.com",
                full_name="Mike Wilson", 
                department="HR",
                role="HR Manager"
            ),
            User(
                username="sarah.johnson",
                email="sarah.johnson@company.com",
                full_name="Sarah Johnson",
                department="Sales",
                role="Sales Representative"
            ),
            User(
                username="admin",
                email="admin@company.com",
                full_name="System Administrator",
                department="IT",
                role="Admin"
            )
        ]
        
        for user in sample_users:
            db.add(user)
        
        db.commit()
        print("✅ Sample users created successfully")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    init_sample_data()
    print("🚀 Database initialization complete!")