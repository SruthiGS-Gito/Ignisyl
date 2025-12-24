"""
Logging Configuration for IGNISYL
Configures structured logging for the entire application
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logging(log_level: str = "INFO", log_to_file: bool = True):
    """
    Setup logging configuration for IGNISYL
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file in addition to console
    """
    
    # Create logs directory
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (rotating)
    if log_to_file:
        log_file = log_dir / f"ignisyl_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        print(f"[INFO] Logging to file: {log_file}")
    
    # Suppress noisy libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('watchdog').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    print(f"[OK] Logging configured (level: {log_level})")
    
    return logger


# Default logger instance
logger = setup_logging()


# Utility functions for structured logging

def log_threat_detection(user_id: str, risk_score: float, risk_level: str, activity_type: str):
    """Log threat detection event"""
    logging.info(
        f"THREAT_DETECTION | user_id={user_id} | activity={activity_type} | "
        f"risk_score={risk_score:.1f} | risk_level={risk_level}"
    )


def log_api_request(endpoint: str, method: str, user_id: str = None, status_code: int = None):
    """Log API request"""
    logging.info(
        f"API_REQUEST | endpoint={endpoint} | method={method} | "
        f"user_id={user_id} | status={status_code}"
    )


def log_ml_prediction(model_name: str, prediction: float, duration_ms: float):
    """Log ML model prediction"""
    logging.debug(
        f"ML_PREDICTION | model={model_name} | prediction={prediction:.2f} | "
        f"duration_ms={duration_ms:.1f}"
    )


def log_firewall_action(user_id: str, action: str, reason: str):
    """Log firewall action"""
    logging.warning(
        f"FIREWALL_ACTION | user_id={user_id} | action={action} | reason={reason}"
    )


def log_error(error_type: str, error_message: str, context: dict = None):
    """Log error with context"""
    context_str = f" | context={context}" if context else ""
    logging.error(f"ERROR | type={error_type} | message={error_message}{context_str}")
