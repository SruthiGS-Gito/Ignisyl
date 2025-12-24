"""
Comprehensive Activity Monitoring System
Monitors multiple threat vectors beyond just network activity
"""

import os
import time
import psutil
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json

class ComprehensiveMonitor:
    """
    Monitors multiple security-relevant activities:
    - Login attempts
    - File access patterns
    - USB device usage
    - Honeypot access
    - Process monitoring
    """
    
    def __init__(self):
        self.monitored_dirs = []
        self.honeypots = []
        self.login_attempts = []
        self.file_accesses = []
        self.usb_devices = []
        
        # Initialize monitoring
        self._setup_honeypots()
        self._get_initial_usb_state()
    
    def _setup_honeypots(self):
        """Create honeypot files (fake sensitive files to catch intruders)"""
        honeypot_dir = Path("data/honeypots")
        honeypot_dir.mkdir(parents=True, exist_ok=True)
        
        # Create fake sensitive files
        honeypot_files = [
            "confidential_salary_data.xlsx",
            "customer_credit_cards.csv",
            "admin_passwords.txt",
            "financial_reports_q4.pdf",
            "trade_secrets.docx"
        ]
        
        for filename in honeypot_files:
            filepath = honeypot_dir / filename
            if not filepath.exists():
                with open(filepath, 'w') as f:
                    f.write(f"HONEYPOT - DO NOT ACCESS\n")
                    f.write(f"This is a decoy file for security monitoring.\n")
                    f.write(f"Access is being logged.\n")
                
                self.honeypots.append({
                    'path': str(filepath),
                    'filename': filename,
                    'created_at': datetime.now().isoformat()
                })
        
        print(f"[OK] Created {len(honeypot_files)} honeypot files")
    
    def check_honeypot_access(self) -> List[Dict]:
        """
        Check if any honeypot files have been accessed
        
        Returns:
            List of honeypot access events
        """
        accesses = []
        
        for honeypot in self.honeypots:
            filepath = Path(honeypot['path'])
            
            if filepath.exists():
                stats = filepath.stat()
                access_time = datetime.fromtimestamp(stats.st_atime)
                modified_time = datetime.fromtimestamp(stats.st_mtime)
                
                # If file was accessed recently (within last 5 minutes)
                time_diff = (datetime.now() - access_time).total_seconds()
                
                if time_diff < 300:  # 5 minutes
                    accesses.append({
                        'honeypot_file': honeypot['filename'],
                        'accessed_at': access_time.isoformat(),
                        'modified_at': modified_time.isoformat(),
                        'severity': 'CRITICAL',
                        'description': f'Unauthorized access to honeypot file: {honeypot["filename"]}'
                    })
        
        return accesses
    
    def _get_initial_usb_state(self):
        """Get initial USB device state"""
        try:
            partitions = psutil.disk_partitions()
            for partition in partitions:
                if 'removable' in partition.opts.lower():
                    self.usb_devices.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'detected_at': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"Error detecting USB devices: {e}")
    
    def detect_usb_activity(self) -> List[Dict]:
        """
        Detect new USB device connections
        
        Returns:
            List of new USB devices detected
        """
        new_devices = []
        current_devices = []
        
        try:
            partitions = psutil.disk_partitions()
            for partition in partitions:
                if 'removable' in partition.opts.lower():
                    current_devices.append(partition.device)
                    
                    # Check if this is a new device
                    if not any(usb['device'] == partition.device for usb in self.usb_devices):
                        device_info = {
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'detected_at': datetime.now().isoformat(),
                            'severity': 'MEDIUM',
                            'description': f'New USB device connected: {partition.device}'
                        }
                        
                        self.usb_devices.append(device_info)
                        new_devices.append(device_info)
        
        except Exception as e:
            print(f"Error detecting USB: {e}")
        
        return new_devices
    
    def monitor_login_attempt(self, username: str, success: bool, 
                             ip_address: str = "127.0.0.1", 
                             timestamp: Optional[str] = None) -> Dict:
        """
        Log a login attempt
        
        Args:
            username: Username attempting login
            success: Whether login was successful
            ip_address: IP address of login attempt
            timestamp: When the attempt occurred
            
        Returns:
            Login attempt record
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # Check for suspicious patterns
        hour = datetime.fromisoformat(timestamp).hour
        is_unusual_time = hour < 6 or hour > 22  # Outside 6 AM - 10 PM
        
        # Check for repeated failed attempts
        recent_failures = [
            attempt for attempt in self.login_attempts
            if attempt['username'] == username 
            and not attempt['success']
            and (datetime.now() - datetime.fromisoformat(attempt['timestamp'])).total_seconds() < 300
        ]
        
        severity = "LOW"
        if not success:
            if len(recent_failures) >= 3:
                severity = "HIGH"
            elif len(recent_failures) >= 1:
                severity = "MEDIUM"
        
        if is_unusual_time and success:
            severity = "MEDIUM"
        
        login_record = {
            'username': username,
            'success': success,
            'ip_address': ip_address,
            'timestamp': timestamp,
            'unusual_time': is_unusual_time,
            'hour': hour,
            'failed_attempts_count': len(recent_failures),
            'severity': severity,
            'description': self._generate_login_description(username, success, is_unusual_time, len(recent_failures))
        }
        
        self.login_attempts.append(login_record)
        return login_record
    
    def _generate_login_description(self, username: str, success: bool, 
                                   unusual_time: bool, failed_count: int) -> str:
        """Generate description for login attempt"""
        if not success:
            if failed_count >= 3:
                return f"Multiple failed login attempts detected for {username} (Total: {failed_count + 1})"
            return f"Failed login attempt for {username}"
        
        if unusual_time:
            return f"Login at unusual time for {username}"
        
        return f"Successful login for {username}"
    
    def monitor_file_access(self, filepath: str, user_id: str, 
                           operation: str = "read") -> Dict:
        """
        Monitor file access activity
        
        Args:
            filepath: Path to file accessed
            user_id: User accessing the file
            operation: Type of operation (read, write, delete)
            
        Returns:
            File access record
        """
        
        if not filepath:
            filepath = "unknown_file"
        
        # Determine sensitivity
        sensitive_keywords = ['password', 'secret', 'confidential', 'admin', 
                             'salary', 'financial', 'credit', 'social_security']
        
        filepath_str = filepath or ""
        is_sensitive = any(keyword in filepath_str.lower() for keyword in sensitive_keywords)
        
        # Check if it's a honeypot
        is_honeypot = any(honeypot['path'] in filepath for honeypot in self.honeypots)
        
        severity = "LOW"
        if is_honeypot:
            severity = "CRITICAL"
        elif is_sensitive and operation == "read":
            severity = "MEDIUM"
        elif is_sensitive and operation in ["write", "delete"]:
            severity = "HIGH"
        
        access_record = {
            'filepath': filepath,
            'filename': Path(filepath).name,
            'user_id': user_id,
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'is_sensitive': is_sensitive,
            'is_honeypot': is_honeypot,
            'severity': severity,
            'description': self._generate_file_access_description(filepath, operation, is_honeypot, is_sensitive)
        }
        
        self.file_accesses.append(access_record)
        return access_record
    
    def _generate_file_access_description(self, filepath: str, operation: str, 
                                         is_honeypot: bool, is_sensitive: bool) -> str:
        """Generate description for file access"""
        # Fix: Assign to a variable!
        filename = Path(filepath).name if filepath else "unknown"
    
        if is_honeypot:
            return f"[ALERT] HONEYPOT TRIGGERED: Unauthorized access to decoy file '{filename}'"
    
        if is_sensitive:
            return f"Access to sensitive file '{filename}' ({operation})"
    
        return f"File access: '{filename}' ({operation})"
    
    def get_suspicious_activities(self, time_window_minutes: int = 60) -> List[Dict]:
        """
        Get all suspicious activities within time window
        
        Args:
            time_window_minutes: Time window to check
            
        Returns:
            List of suspicious activities
        """
        cutoff_time = datetime.now().timestamp() - (time_window_minutes * 60)
        suspicious = []
        
        # Check login attempts
        for login in self.login_attempts:
            login_time = datetime.fromisoformat(login['timestamp']).timestamp()
            if login_time > cutoff_time and login['severity'] in ['MEDIUM', 'HIGH', 'CRITICAL']:
                suspicious.append({
                    'type': 'login_attempt',
                    'severity': login['severity'],
                    'data': login
                })
        
        # Check file accesses
        for access in self.file_accesses:
            access_time = datetime.fromisoformat(access['timestamp']).timestamp()
            if access_time > cutoff_time and access['severity'] in ['MEDIUM', 'HIGH', 'CRITICAL']:
                suspicious.append({
                    'type': 'file_access',
                    'severity': access['severity'],
                    'data': access
                })
        
        # Check honeypot access
        honeypot_accesses = self.check_honeypot_access()
        for access in honeypot_accesses:
            suspicious.append({
                'type': 'honeypot_access',
                'severity': 'CRITICAL',
                'data': access
            })
        
        # Check USB activity
        usb_activity = self.detect_usb_activity()
        for usb in usb_activity:
            suspicious.append({
                'type': 'usb_device',
                'severity': 'MEDIUM',
                'data': usb
            })
        
        return sorted(suspicious, key=lambda x: x['data'].get('timestamp', ''), reverse=True)

# Global instance
comprehensive_monitor = ComprehensiveMonitor()