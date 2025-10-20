"""
Input Validation Utilities for IGNISYL
Validates user inputs, API requests, and data integrity
"""

from typing import Dict, List, Any, Optional
import re
from datetime import datetime

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_username(username: str) -> tuple:
    """
    Validate username format
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return (False, "Username cannot be empty")
    
    if len(username) < 3:
        return (False, "Username must be at least 3 characters")
    
    if len(username) > 50:
        return (False, "Username must be less than 50 characters")
    
    # Only alphanumeric and underscore
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return (False, "Username can only contain letters, numbers, and underscores")
    
    return (True, "")

def validate_user_data(user_data: Dict) -> tuple:
    """
    Validate user registration data
    
    Args:
        user_data: Dictionary with user information
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['username', 'full_name', 'department', 'role', 'email']
    
    # Check required fields
    for field in required_fields:
        if field not in user_data or not user_data[field]:
            return (False, f"Missing required field: {field}")
    
    # Validate username
    is_valid, error = validate_username(user_data['username'])
    if not is_valid:
        return (False, error)
    
    # Validate email
    if not validate_email(user_data['email']):
        return (False, "Invalid email format")
    
    # Validate full_name
    if len(user_data['full_name']) < 2:
        return (False, "Full name must be at least 2 characters")
    
    return (True, "")

def validate_activity_data(activity_data: Dict) -> tuple:
    """
    Validate activity data for threat detection
    
    Args:
        activity_data: Dictionary with activity information
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['user_id', 'activity_type', 'timestamp']
    
    # Check required fields
    for field in required_fields:
        if field not in activity_data:
            return (False, f"Missing required field: {field}")
    
    # Validate timestamp format
    try:
        datetime.fromisoformat(activity_data['timestamp'].replace('Z', '+00:00'))
    except Exception:
        return (False, "Invalid timestamp format")
    
    # Validate numeric fields if present
    numeric_fields = ['file_size', 'bytes_transferred', 'risk_score']
    for field in numeric_fields:
        if field in activity_data:
            try:
                float(activity_data[field])
            except (ValueError, TypeError):
                return (False, f"Invalid numeric value for {field}")
    
    return (True, "")

def validate_risk_score(risk_score: float) -> bool:
    """
    Validate risk score is within valid range
    
    Args:
        risk_score: Risk score to validate
        
    Returns:
        True if valid (0-100), False otherwise
    """
    try:
        score = float(risk_score)
        return 0 <= score <= 100
    except (ValueError, TypeError):
        return False

def validate_ip_address(ip: str) -> bool:
    """
    Validate IPv4 address format
    
    Args:
        ip: IP address string
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    
    # Check each octet is 0-255
    octets = ip.split('.')
    for octet in octets:
        if int(octet) > 255:
            return False
    
    return True

def validate_port(port: int) -> bool:
    """
    Validate network port number
    
    Args:
        port: Port number
        
    Returns:
        True if valid (1-65535), False otherwise
    """
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = filename.replace('/', '').replace('\\', '')
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename

def validate_date_range(start_date: str, end_date: str) -> tuple:
    """
    Validate date range
    
    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if start > end:
            return (False, "Start date must be before end date")
        
        # Check if range is reasonable (not more than 1 year)
        if (end - start).days > 365:
            return (False, "Date range cannot exceed 1 year")
        
        return (True, "")
    except Exception as e:
        return (False, f"Invalid date format: {str(e)}")