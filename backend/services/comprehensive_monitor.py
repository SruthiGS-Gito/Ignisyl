"""
Comprehensive Activity Monitoring System for IGNISYL
Monitors honeypots, USB devices, login attempts, and file access
"""

import os
import sys
import time
import psutil
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
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

class ComprehensiveMonitor:
    """
    Monitors multiple security-relevant activities:
    - Login attempts
    - File access patterns
    - USB device usage
    - Honeypot access
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
        honeypot_dir = Path(settings.DATA_PATH) / "honeypots"
        honeypot_dir.mkdir(parents=True, exist_ok=True)
        
        # Create fake sensitive files
        honeypot_files = [
            ("confidential_salary_data.xlsx", "Salary information"),
            ("customer_credit_cards.csv", "Payment card data"),
            ("admin_passwords.txt", "Administrative credentials"),
            ("financial_reports_q4.pdf", "Financial statements"),
            ("trade_secrets.docx", "Proprietary information")
        ]
        
        created_count = 0
        for filename, description in honeypot_files:
            filepath = honeypot_dir / filename
            
            if not filepath.exists():
                try:
                    with open(filepath, 'w') as f:
                        f.write(f"🚨 HONEYPOT FILE - DO NOT ACCESS 🚨\n")
                        f.write(f"Type: {description}\n")
                        f.write(f"This is a decoy file for security monitoring.\n")
                        f.write(f"All access attempts are logged and reported.\n")
                        f.write(f"Created: {datetime.now().isoformat()}\n")
                    
                    created_count += 1
                except Exception as e:
                    logger.error(f"Failed to create honeypot {filename}: {e}")
                    continue
            
            self.honeypots.append({
                'path': str(filepath),
                'filename': filename,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'last_checked': None,
                'access_count': 0
            })
        
        logger.info(f"✅ Created {created_count} honeypot files in {honeypot_dir}")
    
    def check_honeypot_access(self) -> List[Dict]:
        """
        Check if any honeypot files have been accessed
        
        Returns:
            List of honeypot access events
        """
        accesses = []
        current_time = datetime.now()
        
        for honeypot in self.honeypots:
            filepath = Path(honeypot['path'])
            
            if not filepath.exists():
                logger.warning(f"Honeypot file missing: {filepath}")
                continue
            
            try:
                stats = filepath.stat()
                access_time = datetime.fromtimestamp(stats.st_atime)
                modified_time = datetime.fromtimestamp(stats.st_mtime)
                
                # Check if accessed recently (last 5 minutes)
                time_since_access = (current_time - access_time).total_seconds()
                
                # If accessed within last 5 minutes and after last check
                if time_since_access < 300:  # 5 minutes
                    last_checked = honeypot.get('last_checked')
                    
                    if last_checked is None or access_time > datetime.fromisoformat(last_checked):
                        accesses.append({
                            'honeypot_file': honeypot['filename'],
                            'honeypot_path': honeypot['path'],
                            'description': honeypot['description'],
                            'accessed_at': access_time.isoformat(),
                            'modified_at': modified_time.isoformat(),
                            'time_since_access_seconds': int(time_since_access),
                            'severity': 'CRITICAL',
                            'alert_message': f'🚨 HONEYPOT TRIGGERED: {honeypot["filename"]}'
                        })
                        
                        # Update last checked time and increment counter
                        honeypot['last_checked'] = current_time.isoformat()
                        honeypot['access_count'] += 1
                
            except Exception as e:
                logger.error(f"Error checking honeypot {honeypot['filename']}: {e}")
        
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
                        'fstype': partition.fstype,
                        'detected_at': datetime.now().isoformat()
                    })
            
            if self.usb_devices:
                logger.info(f"Detected {len(self.usb_devices)} existing USB devices")
        except Exception as e:
            logger.error(f"Error detecting initial USB devices: {e}")
    
    def detect_usb_activity(self) -> List[Dict]:
        """
        Detect new USB device connections
        
        Returns:
            List of new USB devices detected
        """
        new_devices = []
        
        try:
            partitions = psutil.disk_partitions()
            current_devices = []
            
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
                            'description': f'New USB device connected: {partition.device}',
                            'alert_message': f'USB Device Connected: {partition.mountpoint}'
                        }
                        
                        self.usb_devices.append(device_info)
                        new_devices.append(device_info)
                        
                        logger.info(f"🔌 New USB device detected: {partition.device}")
        
        except Exception as e:
            logger.error(f"Error detecting USB activity: {e}")
        
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
        
        login_time = datetime.fromisoformat(timestamp)
        hour = login_time.hour
        
        # Check for unusual time (outside 6 AM - 10 PM)
        is_unusual_time = hour < 6 or hour > 22
        
        # Check for repeated failed attempts in last 5 minutes
        five_mins_ago = datetime.now() - timedelta(minutes=5)
        recent_failures = [
            attempt for attempt in self.login_attempts
            if attempt['username'] == username 
            and not attempt['success']
            and datetime.fromisoformat(attempt['timestamp']) > five_mins_ago
        ]
        
        # Determine severity
        severity = "LOW"
        if not success:
            if len(recent_failures) >= 3:
                severity = "HIGH"
            elif len(recent_failures) >= 1:
                severity = "MEDIUM"
        elif is_unusual_time:
            severity = "MEDIUM"
        
        login_record = {
            'username': username,
            'success': success,
            'ip_address': ip_address,
            'timestamp': timestamp,
            'hour': hour,
            'unusual_time': is_unusual_time,
            'failed_attempts_count': len(recent_failures),
            'severity': severity,
            'description': self._generate_login_description(
                username, success, is_unusual_time, len(recent_failures)
            )
        }
        
        self.login_attempts.append(login_record)
        
        if severity in ['HIGH', 'CRITICAL']:
            logger.warning(f"⚠️ {login_record['description']}")
        
        return login_record
    
    def _generate_login_description(self, username: str, success: bool, 
                                   unusual_time: bool, failed_count: int) -> str:
        """Generate description for login attempt"""
        if not success:
            if failed_count >= 3:
                return f"🚨 Multiple failed login attempts for {username} (Total: {failed_count + 1})"
            return f"Failed login attempt for {username}"
        
        if unusual_time:
            return f"⚠️ Login at unusual time for {username}"
        
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
        # Determine sensitivity
        sensitive_keywords = [
            'password', 'secret', 'confidential', 'admin', 
            'salary', 'financial', 'credit', 'social_security',
            'ssn', 'payroll', 'classified', 'private'
        ]
        
        filepath_lower = filepath.lower()
        is_sensitive = any(keyword in filepath_lower for keyword in sensitive_keywords)
        
        # Check if it's a honeypot
        is_honeypot = any(honeypot['path'] in filepath for honeypot in self.honeypots)
        
        # Determine severity
        severity = "LOW"
        if is_honeypot:
            severity = "CRITICAL"
        elif is_sensitive and operation == "read":
            severity = "MEDIUM"
        elif is_sensitive and operation in ["write", "delete", "modify"]:
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
            'description': self._generate_file_access_description(
                filepath, operation, is_honeypot, is_sensitive
            )
        }
        
        self.file_accesses.append(access_record)
        
        if severity in ['HIGH', 'CRITICAL']:
            logger.warning(f"⚠️ {access_record['description']}")
        
        return access_record
    
    def _generate_file_access_description(self, filepath: str, operation: str, 
                                         is_honeypot: bool, is_sensitive: bool) -> str:
        """Generate description for file access"""
        filename = Path(filepath).name
        
        if is_honeypot:
            return f"🚨 HONEYPOT TRIGGERED: Unauthorized access to '{filename}'"
        
        if is_sensitive:
            return f"Access to sensitive file '{filename}' ({operation})"
        
        return f"File access: '{filename}' ({operation})"
    
    def get_suspicious_activities(self, time_window_minutes: int = 60) -> List[Dict]:
        """
        Get all suspicious activities within time window
        
        Args:
            time_window_minutes: Time window to check (minutes)
            
        Returns:
            List of suspicious activities
        """
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        suspicious = []
        
        # Check login attempts
        for login in self.login_attempts:
            login_time = datetime.fromisoformat(login['timestamp'])
            if login_time > cutoff_time and login['severity'] in ['MEDIUM', 'HIGH', 'CRITICAL']:
                suspicious.append({
                    'type': 'login_attempt',
                    'severity': login['severity'],
                    'timestamp': login['timestamp'],
                    'data': login
                })
        
        # Check file accesses
        for access in self.file_accesses:
            access_time = datetime.fromisoformat(access['timestamp'])
            if access_time > cutoff_time and access['severity'] in ['MEDIUM', 'HIGH', 'CRITICAL']:
                suspicious.append({
                    'type': 'file_access',
                    'severity': access['severity'],
                    'timestamp': access['timestamp'],
                    'data': access
                })
        
        # Check honeypot access
        honeypot_accesses = self.check_honeypot_access()
        for access in honeypot_accesses:
            suspicious.append({
                'type': 'honeypot_access',
                'severity': 'CRITICAL',
                'timestamp': access['accessed_at'],
                'data': access
            })
        
        # Check USB activity
        usb_activity = self.detect_usb_activity()
        for usb in usb_activity:
            suspicious.append({
                'type': 'usb_device',
                'severity': 'MEDIUM',
                'timestamp': usb['detected_at'],
                'data': usb
            })
        
        # Sort by timestamp (most recent first)
        suspicious.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return suspicious
    
    def get_stats(self) -> Dict:
        """Get monitoring statistics"""
        return {
            'honeypots': {
                'total': len(self.honeypots),
                'total_accesses': sum(h.get('access_count', 0) for h in self.honeypots)
            },
            'login_attempts': {
                'total': len(self.login_attempts),
                'successful': len([l for l in self.login_attempts if l['success']]),
                'failed': len([l for l in self.login_attempts if not l['success']])
            },
            'file_accesses': {
                'total': len(self.file_accesses),
                'sensitive': len([f for f in self.file_accesses if f['is_sensitive']]),
                'honeypot': len([f for f in self.file_accesses if f['is_honeypot']])
            },
            'usb_devices': {
                'total': len(self.usb_devices)
            }
        }
    
    def clear_old_records(self, days: int = 7):
        """Clear records older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Clear old login attempts
        self.login_attempts = [
            l for l in self.login_attempts
            if datetime.fromisoformat(l['timestamp']) > cutoff_time
        ]
        
        # Clear old file accesses
        self.file_accesses = [
            f for f in self.file_accesses
            if datetime.fromisoformat(f['timestamp']) > cutoff_time
        ]
        
        logger.info(f"Cleared records older than {days} days")

# Global instance
try:
    comprehensive_monitor = ComprehensiveMonitor()
except Exception as e:
    logger.error(f"Failed to initialize comprehensive monitor: {e}")
    comprehensive_monitor = None

def main():
    """Test comprehensive monitor"""
    print("\n" + "="*60)
    print("IGNISYL Comprehensive Monitor Test")
    print("="*60 + "\n")
    
    monitor = ComprehensiveMonitor()
    
    # Check honeypots
    print("📁 Honeypot files:")
    for hp in monitor.honeypots:
        print(f"   - {hp['filename']}: {hp['description']}")
    
    # Check for suspicious activities
    suspicious = monitor.get_suspicious_activities(60)
    print(f"\n⚠️ Suspicious activities (last hour): {len(suspicious)}")
    
    # Get stats
    stats = monitor.get_stats()
    print(f"\n📊 Statistics:")
    for category, data in stats.items():
        print(f"   {category}: {data}")
    
    print("\n✅ Comprehensive monitor test complete!")

if __name__ == "__main__":
    main()