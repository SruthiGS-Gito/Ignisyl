"""
Helper Utilities for IGNISYL
Common utility functions used across the project
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import hashlib
import json

def format_bytes(bytes_value: int) -> str:
    """
    Convert bytes to human-readable format
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 GB", "256 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def format_timestamp(timestamp: str, format_type: str = "readable") -> str:
    """
    Format ISO timestamp to readable format
    
    Args:
        timestamp: ISO format timestamp string
        format_type: "readable", "date", "time", or "relative"
        
    Returns:
        Formatted timestamp string
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        if format_type == "readable":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "date":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "time":
            return dt.strftime("%H:%M:%S")
        elif format_type == "relative":
            now = datetime.now()
            diff = now - dt
            
            if diff.days > 0:
                return f"{diff.days} days ago"
            elif diff.seconds >= 3600:
                return f"{diff.seconds // 3600} hours ago"
            elif diff.seconds >= 60:
                return f"{diff.seconds // 60} minutes ago"
            else:
                return "Just now"
        else:
            return timestamp
    except Exception as e:
        return timestamp

def calculate_risk_score(factors: Dict[str, float], weights: Dict[str, float] = None) -> float:
    """
    Calculate weighted risk score from multiple factors
    
    Args:
        factors: Dictionary of factor names and their values
        weights: Optional custom weights for factors
        
    Returns:
        Calculated risk score (0-100)
    """
    if weights is None:
        # Default weights
        weights = {
            'time_anomaly': 0.25,
            'data_volume': 0.30,
            'access_pattern': 0.20,
            'location': 0.15,
            'behavior': 0.10
        }
    
    total_score = 0.0
    total_weight = 0.0
    
    for factor_name, factor_value in factors.items():
        weight = weights.get(factor_name, 0.1)
        total_score += factor_value * weight
        total_weight += weight
    
    # Normalize to 0-100
    if total_weight > 0:
        final_score = (total_score / total_weight) * 100
        return min(max(final_score, 0), 100)  # Clamp between 0-100
    
    return 0.0

def hash_data(data: str, algorithm: str = "sha256") -> str:
    """
    Hash sensitive data
    
    Args:
        data: Data to hash
        algorithm: Hashing algorithm (md5, sha1, sha256)
        
    Returns:
        Hashed string
    """
    if algorithm == "md5":
        return hashlib.md5(data.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(data.encode()).hexdigest()
    else:  # default sha256
        return hashlib.sha256(data.encode()).hexdigest()

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`']
    sanitized = text
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Truncate to max length
    return sanitized[:max_length]

def get_time_window(window_type: str) -> tuple:
    """
    Get start and end datetime for a time window
    
    Args:
        window_type: "today", "yesterday", "week", "month"
        
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    now = datetime.now()
    
    if window_type == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif window_type == "yesterday":
        start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif window_type == "week":
        start = now - timedelta(days=7)
        end = now
    elif window_type == "month":
        start = now - timedelta(days=30)
        end = now
    else:
        start = now
        end = now
    
    return (start, end)

def export_to_json(data: Any, filepath: str = None) -> str:
    """
    Export data to JSON format
    
    Args:
        data: Data to export
        filepath: Optional file path to save
        
    Returns:
        JSON string
    """
    json_str = json.dumps(data, indent=2, default=str)
    
    if filepath:
        with open(filepath, 'w') as f:
            f.write(json_str)
    
    return json_str

def parse_user_agent(user_agent_string: str) -> Dict:
    """
    Parse user agent string to extract browser and OS info
    
    Args:
        user_agent_string: User agent string
        
    Returns:
        Dictionary with browser, os, device info
    """
    result = {
        "browser": "Unknown",
        "os": "Unknown",
        "device": "Desktop"
    }
    
    # Simple parsing (can be enhanced with user-agents library)
    if "Windows" in user_agent_string:
        result["os"] = "Windows"
    elif "Mac" in user_agent_string:
        result["os"] = "macOS"
    elif "Linux" in user_agent_string:
        result["os"] = "Linux"
    
    if "Chrome" in user_agent_string:
        result["browser"] = "Chrome"
    elif "Firefox" in user_agent_string:
        result["browser"] = "Firefox"
    elif "Safari" in user_agent_string:
        result["browser"] = "Safari"
    
    if "Mobile" in user_agent_string or "Android" in user_agent_string:
        result["device"] = "Mobile"
    elif "Tablet" in user_agent_string or "iPad" in user_agent_string:
        result["device"] = "Tablet"
    
    return result