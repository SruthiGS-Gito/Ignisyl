"""
IGNISYL Configuration Module
Main configuration settings for the AI-Powered Insider Threat Detection System
"""
# This file : Stores all system settings and configuration values
# - Database connection paths
# - API server settings (host, port)
# - Risk score thresholds (low, medium, high)
# - Creates necessary directories for data storage

import os
from pathlib import Path
from typing import Optional

# Handle pydantic_settings import gracefully
try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        # Fallback for basic functionality
        class BaseSettings:
            def __init__(self):
                pass

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application Settings
    APP_NAME: str = "IGNISYL - AI Insider Threat Detection"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API Settings
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # Database Settings
    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT}/data/ignisyl.db"
    
    # Security Settings
    SECRET_KEY: str = "ignisyl-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Machine Learning Settings
    MODEL_PATH: str = str(PROJECT_ROOT / "data" / "models")
    DATA_PATH: str = str(PROJECT_ROOT / "data")
    
    # Risk Assessment Thresholds
    LOW_RISK_THRESHOLD: float = 30.0
    MEDIUM_RISK_THRESHOLD: float = 70.0
    HIGH_RISK_THRESHOLD: float = 100.0
    
    # Firewall Settings
    FIREWALL_ENABLED: bool = True
    AUTO_BLOCK_HIGH_RISK: bool = True
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = str(PROJECT_ROOT / "data" / "logs" / "application.log")
    
    # Real-time Processing
    WEBSOCKET_ENABLED: bool = True
    REAL_TIME_PROCESSING: bool = True
    
    # Data Generation (for demo purposes)
    SYNTHETIC_DATA_ENABLED: bool = True
    DEMO_USERS_COUNT: int = 50
    DEMO_ACTIVITIES_COUNT: int = 10000
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Risk Level Mappings
RISK_LEVELS = {
    "LOW": (0, settings.LOW_RISK_THRESHOLD),
    "MEDIUM": (settings.LOW_RISK_THRESHOLD, settings.MEDIUM_RISK_THRESHOLD),
    "HIGH": (settings.MEDIUM_RISK_THRESHOLD, settings.HIGH_RISK_THRESHOLD)
}

# Firewall Actions
FIREWALL_ACTIONS = {
    "ALLOW": "allow",
    "RESTRICT": "restrict", 
    "BLOCK": "block"
}

# Activity Types for Monitoring
ACTIVITY_TYPES = [
    "login",
    "file_access",
    "file_download",
    "file_upload",
    "network_access",
    "system_command",
    "database_query",
    "email_sent",
    "usb_access",
    "application_launch"
]

# Network Protocols to Monitor
MONITORED_PROTOCOLS = [
    "HTTP",
    "HTTPS", 
    "FTP",
    "SSH",
    "SMTP",
    "POP3",
    "IMAP",
    "DNS"
]

def get_database_url() -> str:
    """Get database URL with proper path resolution"""
    db_path = PROJECT_ROOT / "data" / "ignisyl.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"

def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "data" / "models",
        PROJECT_ROOT / "data" / "logs",
        PROJECT_ROOT / "data" / "synthetic",
        PROJECT_ROOT / "data" / "reports",
        PROJECT_ROOT / "data" / "honeypots",
        PROJECT_ROOT / "data" / "sessions"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Created necessary directories for {settings.APP_NAME}")

if __name__ == "__main__":
    ensure_directories()
    print(f"Configuration loaded for {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Model Path: {settings.MODEL_PATH}")
