"""
Synthetic Data Generator for IGNISYL
Generates realistic user behavior patterns with embedded anomalies for ML training
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import json
import os
import sys
from faker import Faker
from typing import List, Dict, Tuple
import ipaddress

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.config import settings, ACTIVITY_TYPES, MONITORED_PROTOCOLS

fake = Faker()

# Configuration constants
SUSPICION_BOOST_OFF_HOURS = 0.6
SUSPICION_BOOST_BUSINESS_HOURS = 0.3
NORMAL_ACTIVITY_SUSPICION_RANGE = (0.1, 0.3)
ANOMALY_BASE_CONFIDENCE_RANGE = (0.6, 0.9)

class BehavioralDataGenerator:
    """Generate realistic user behavior data with anomalies for ML training"""
    
    def __init__(self, num_users: int = 50, num_days: int = 30):
        self.num_users = num_users
        self.num_days = num_days
        self.users = []
        self.user_profiles = {}
        self.activities = []
        
        # Business context patterns
        self.business_cycles = {
            'month_end': [28, 29, 30, 31, 1, 2, 3],
            'quarter_end': [89, 90, 91, 1, 2, 3],
            'maintenance_windows': [0, 6],  # Sunday, Saturday
        }
        
        # Threat scenarios for anomaly injection (configurable percentages)
        self.threat_scenarios = {
            'data_exfiltration': 0.02,      # 2% of users
            'privilege_abuse': 0.03,        # 3% of users  
            'credential_compromise': 0.01,  # 1% of users
            'insider_sabotage': 0.005,      # 0.5% of users
        }
        
        # Business domains (common enterprise services)
        self.business_domains = [
            'salesforce.com', 'microsoft.com', 'google.com', 'amazonaws.com',
            'office365.com', 'github.com', 'slack.com', 'zoom.us', 'dropbox.com',
            'atlassian.com', 'adobe.com', 'servicenow.com', 'workday.com'
        ]
        
    def generate_user_profiles(self) -> List[Dict]:
        """Generate diverse user profiles with realistic behavioral patterns"""
        departments = ['IT', 'Finance', 'HR', 'Sales', 'Marketing', 'Operations', 'Legal']
        roles = {
            'IT': ['Software Engineer', 'System Admin', 'DevOps Engineer', 'Security Analyst'],
            'Finance': ['Financial Analyst', 'Accountant', 'Controller', 'CFO'],
            'HR': ['HR Manager', 'Recruiter', 'HR Coordinator', 'CHRO'],
            'Sales': ['Sales Rep', 'Sales Manager', 'Account Manager', 'VP Sales'],
            'Marketing': ['Marketing Manager', 'Content Creator', 'Digital Marketer', 'CMO'],
            'Operations': ['Operations Manager', 'Supply Chain Analyst', 'COO'],
            'Legal': ['Legal Counsel', 'Paralegal', 'Chief Legal Officer']
        }
        
        for i in range(self.num_users):
            dept = random.choice(departments)
            role = random.choice(roles[dept])
            
            # Generate proper user ID format
            user_id = f"user_{str(i + 1).zfill(3)}"
            
            user = {
                'user_id': user_id,
                'username': fake.user_name(),
                'email': fake.email(),
                'full_name': fake.name(),
                'department': dept,
                'role': role,
                'seniority_level': random.choice(['Junior', 'Mid', 'Senior', 'Lead', 'Executive']),
                'start_date': fake.date_between(start_date='-5y', end_date='today'),
                'work_hours': self._generate_work_pattern(dept, role),
                'device_preferences': self._generate_device_profile(),
                'network_patterns': self._generate_network_profile(dept),
                'file_access_patterns': self._generate_file_patterns(dept, role),
                'is_high_privilege': role in ['System Admin', 'CFO', 'CHRO', 'VP Sales', 'CMO', 'COO', 'Chief Legal Officer'],
                'risk_factors': self._assign_risk_factors()
            }
            
            self.users.append(user)
            self.user_profiles[user['user_id']] = user
            
        return self.users
    
    def _generate_work_pattern(self, dept: str, role: str) -> Dict:
        """Generate realistic work hour patterns based on department and role"""
        base_patterns = {
            'IT': {'start': 9, 'end': 18, 'flexibility': 2, 'weekend_work': 0.1},
            'Finance': {'start': 8, 'end': 17, 'flexibility': 1, 'weekend_work': 0.05},
            'HR': {'start': 9, 'end': 17, 'flexibility': 1, 'weekend_work': 0.02},
            'Sales': {'start': 8, 'end': 19, 'flexibility': 3, 'weekend_work': 0.15},
            'Marketing': {'start': 9, 'end': 18, 'flexibility': 2, 'weekend_work': 0.08},
            'Operations': {'start': 8, 'end': 17, 'flexibility': 1, 'weekend_work': 0.12},
            'Legal': {'start': 9, 'end': 18, 'flexibility': 1, 'weekend_work': 0.05}
        }
        
        pattern = base_patterns[dept].copy()
        
        # Executives work longer and more flexible hours
        executive_titles = ['VP', 'CEO', 'CFO', 'COO', 'CMO', 'CHRO', 'CTO', 'Chief']
        if any(title in role for title in executive_titles):
            pattern['start'] -= 1
            pattern['end'] += 2
            pattern['flexibility'] += 1
            pattern['weekend_work'] += 0.1
            
        return pattern
    
    def _generate_device_profile(self) -> Dict:
        """Generate device usage patterns"""
        devices = ['Windows-Laptop', 'MacBook', 'Linux-Workstation', 'iPhone', 'Android', 'iPad']
        primary_device = random.choice(devices[:3])  # Work devices
        
        return {
            'primary_device': primary_device,
            'secondary_devices': random.sample(devices, random.randint(1, 3)),
            'os_preference': primary_device.split('-')[0],
            'browser_preference': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
            'mobile_usage': random.uniform(0.1, 0.4)
        }
    
    def _generate_network_profile(self, dept: str) -> Dict:
        """Generate network usage patterns by department"""
        base_bandwidth = {
            'IT': random.uniform(2000, 10000),
            'Finance': random.uniform(500, 2000),
            'HR': random.uniform(300, 1000),
            'Sales': random.uniform(800, 3000),
            'Marketing': random.uniform(1000, 5000),
            'Operations': random.uniform(600, 2500),
            'Legal': random.uniform(400, 1500)
        }
        
        return {
            'avg_daily_bandwidth_mb': base_bandwidth[dept],
            'peak_hours': random.choice([[9, 11], [13, 15], [15, 17]]),
            'external_sites_accessed': random.randint(10, 50),
            'vpn_usage': random.uniform(0.1, 0.8),
            'cloud_service_usage': random.uniform(0.3, 0.9)
        }
    
    def _generate_file_patterns(self, dept: str, role: str) -> Dict:
        """Generate file access patterns"""
        file_types = {
            'IT': ['.py', '.js', '.sql', '.log', '.config', '.json'],
            'Finance': ['.xlsx', '.csv', '.pdf', '.docx', '.xlsm'],
            'HR': ['.docx', '.pdf', '.xlsx', '.pptx'],
            'Sales': ['.pdf', '.pptx', '.docx', '.xlsx', '.crm'],
            'Marketing': ['.jpg', '.png', '.mp4', '.pdf', '.psd', '.ai'],
            'Operations': ['.xlsx', '.pdf', '.docx', '.csv'],
            'Legal': ['.pdf', '.docx', '.xlsx', '.legal']
        }
        
        return {
            'file_types': file_types.get(dept, ['.docx', '.pdf', '.xlsx']),
            'avg_files_per_day': random.randint(10, 100),
            'large_file_frequency': random.uniform(0.05, 0.3),
            'sensitive_file_access': 0.5 if 'Senior' in role or 'Lead' in role else 0.2,
            'external_shares': random.uniform(0.02, 0.15)
        }
    
    def _assign_risk_factors(self) -> Dict:
        """Assign risk factors for anomaly generation"""
        return {
            'financial_stress': random.choice([True, False]) if random.random() < 0.1 else False,
            'job_dissatisfaction': random.choice([True, False]) if random.random() < 0.15 else False,
            'recent_performance_issues': random.choice([True, False]) if random.random() < 0.08 else False,
            'external_relationships': random.choice([True, False]) if random.random() < 0.05 else False,
            'access_creep': random.choice([True, False]) if random.random() < 0.2 else False,
        }
    
    def generate_normal_activities(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Generate normal user activities based on behavioral patterns"""
        activities = []
        current_date = start_date
        
        while current_date <= end_date:
            for user in self.users:
                daily_activities = self._generate_daily_activities(user, current_date)
                activities.extend(daily_activities)
            current_date += timedelta(days=1)
            
        return activities
    
    def _generate_daily_activities(self, user: Dict, date: datetime) -> List[Dict]:
        """Generate activities for a single user on a single day"""
        activities = []
        work_pattern = user['work_hours']
        
        # Skip weekend activities based on probability
        if date.weekday() >= 5 and random.random() > work_pattern['weekend_work']:
            return activities
            
        # Determine work hours for this day
        start_hour = max(6, work_pattern['start'] + random.randint(-work_pattern['flexibility'], work_pattern['flexibility']))
        end_hour = min(22, work_pattern['end'] + random.randint(-work_pattern['flexibility'], work_pattern['flexibility']))
        
        # Generate login activity
        login_time = date.replace(hour=start_hour, minute=random.randint(0, 59))
        activities.append(self._create_activity(user, 'login', login_time, {'success': True}))
        
        # Generate activities throughout the day
        current_time = login_time
        while current_time.hour < end_hour:
            activity_type = self._choose_activity_type(user, current_time)
            activity = self._create_activity(user, activity_type, current_time)
            activities.append(activity)
            
            # Move to next activity (15-120 minutes later)
            current_time += timedelta(minutes=random.randint(15, 120))
            
        # Generate logout activity
        logout_time = date.replace(hour=end_hour, minute=random.randint(0, 59))
        activities.append(self._create_activity(user, 'logout', logout_time))
        
        return activities
    
    def _choose_activity_type(self, user: Dict, current_time: datetime) -> str:
        """Choose activity type based on user profile and time"""
        dept_activities = {
            'IT': ['file_access', 'system_command', 'database_query', 'network_access', 'application_launch'],
            'Finance': ['file_access', 'database_query', 'email_sent', 'application_launch', 'file_download'],
            'HR': ['file_access', 'email_sent', 'application_launch', 'database_query'],
            'Sales': ['email_sent', 'file_access', 'network_access', 'application_launch', 'file_upload'],
            'Marketing': ['file_access', 'file_upload', 'network_access', 'application_launch', 'email_sent'],
            'Operations': ['file_access', 'database_query', 'system_command', 'network_access'],
            'Legal': ['file_access', 'email_sent', 'database_query', 'application_launch']
        }
        
        possible_activities = dept_activities.get(user['department'], ACTIVITY_TYPES)
        return random.choice(possible_activities)
    
    def _create_activity(self, user: Dict, activity_type: str, timestamp: datetime, extra_data: Dict = None) -> Dict:
        """Create a single activity record"""
        base_activity = {
            'user_id': user['user_id'],
            'username': user['username'],
            'activity_type': activity_type,
            'timestamp': timestamp,
            'source_ip': self._generate_ip_address(user),
            'user_agent': self._generate_user_agent(user),
            'device_info': self._generate_device_info(user),
            'is_suspicious': False,
            'confidence_score': random.uniform(*NORMAL_ACTIVITY_SUSPICION_RANGE)
        }
        
        # Add activity-specific details
        activity_generators = {
            'file_access': self._generate_file_activity,
            'network_access': self._generate_network_activity,
            'email_sent': self._generate_email_activity,
            'file_download': lambda u: self._generate_file_transfer_activity(u, 'download'),
            'file_upload': lambda u: self._generate_file_transfer_activity(u, 'upload'),
            'database_query': self._generate_database_activity,
            'system_command': self._generate_system_activity,
            'application_launch': self._generate_application_activity,
            'usb_access': self._generate_usb_activity
        }
        
        generator = activity_generators.get(activity_type)
        if generator:
            base_activity.update(generator(user))
            
        if extra_data:
            base_activity.update(extra_data)
            
        return base_activity
    
    def _generate_ip_address(self, user: Dict) -> str:
        """Generate realistic IP addresses"""
        # 80% internal, 20% external (VPN, remote work)
        if random.random() < 0.8:
            # Internal IP ranges
            return str(ipaddress.IPv4Address(random.randint(
                int(ipaddress.IPv4Address('192.168.1.1')),
                int(ipaddress.IPv4Address('192.168.1.254'))
            )))
        else:
            # External IP (VPN or remote)
            return fake.ipv4()
    
    def _generate_user_agent(self, user: Dict) -> str:
        """Generate realistic user agent strings"""
        browsers = {
            'Chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Firefox': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Safari': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Edge': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        }
        
        browser = user['device_preferences']['browser_preference']
        return browsers.get(browser, browsers['Chrome'])
    
    def _generate_device_info(self, user: Dict) -> str:
        """Generate device information"""
        device = user['device_preferences']['primary_device']
        return f"{device}_{random.randint(1000, 9999)}"
    
    def _generate_file_activity(self, user: Dict) -> Dict:
        """Generate file access activity details with realistic file sizes per type"""
        file_patterns = user['file_access_patterns']
        file_type = random.choice(file_patterns['file_types'])
        
        # Realistic file size ranges by type
        file_size_ranges = {
            '.xlsx': (10 * 1024, 5 * 1024 * 1024),      # 10KB to 5MB
            '.csv': (1024, 50 * 1024 * 1024),          # 1KB to 50MB
            '.pdf': (50 * 1024, 10 * 1024 * 1024),     # 50KB to 10MB
            '.docx': (10 * 1024, 2 * 1024 * 1024),     # 10KB to 2MB
            '.pptx': (100 * 1024, 20 * 1024 * 1024),   # 100KB to 20MB
            '.jpg': (100 * 1024, 5 * 1024 * 1024),     # 100KB to 5MB
            '.png': (50 * 1024, 10 * 1024 * 1024),     # 50KB to 10MB
            '.mp4': (1024 * 1024, 500 * 1024 * 1024),  # 1MB to 500MB
            '.py': (1024, 100 * 1024),                 # 1KB to 100KB
            '.js': (1024, 500 * 1024),                 # 1KB to 500KB
            '.log': (1024, 10 * 1024 * 1024),          # 1KB to 10MB
            '.sql': (512, 50 * 1024),                  # 512B to 50KB
        }
        
        size_range = file_size_ranges.get(file_type, (1024, 5 * 1024 * 1024))
        file_size = random.randint(*size_range)
        
        # Generate realistic file paths
        file_paths = {
            '.xlsx': f"/finance/reports/Q{random.randint(1,4)}_2024{file_type}",
            '.py': f"/src/modules/{fake.word()}{file_type}",
            '.pdf': f"/documents/policies/{fake.word()}{file_type}",
            '.docx': f"/documents/{fake.word()}_document{file_type}",
            '.jpg': f"/marketing/assets/{fake.word()}{file_type}",
            '.sql': f"/database/queries/{fake.word()}_query{file_type}",
            '.log': f"/logs/{fake.date()}/application{file_type}"
        }
        
        file_path = file_paths.get(file_type, f"/files/{fake.word()}{file_type}")
        
        return {
            'file_path': file_path,
            'file_size': file_size,
            'action': random.choice(['read', 'write', 'delete', 'copy', 'move']),
            'permission_level': random.choice(['read', 'write', 'admin'])
        }
    
    def _generate_network_activity(self, user: Dict) -> Dict:
        """Generate network access activity details"""
        protocols = random.choice(MONITORED_PROTOCOLS)
        
        return {
            'destination_ip': fake.ipv4(),
            'destination_domain': random.choice(self.business_domains),
            'protocol': protocols,
            'port': random.choice([80, 443, 22, 21, 25, 53, 993, 995]),
            'bytes_transferred': random.randint(1024, 10 * 1024 * 1024),
            'duration_seconds': random.randint(1, 3600),
            'connection_status': random.choice(['established', 'closed', 'timeout'])
        }
    
    def _generate_email_activity(self, user: Dict) -> Dict:
        """Generate email activity details"""
        return {
            'recipient_count': random.randint(1, 20),
            'external_recipients': random.randint(0, 5),
            'attachment_count': random.randint(0, 3),
            'total_attachment_size': random.randint(0, 25 * 1024 * 1024),
            'subject_classification': random.choice(['business', 'personal', 'marketing', 'security']),
            'sender_reputation': random.uniform(0.8, 1.0)
        }
    
    def _generate_file_transfer_activity(self, user: Dict, activity_type: str) -> Dict:
        """Generate file upload/download activity details"""
        return {
            'file_count': random.randint(1, 10),
            'total_size': random.randint(1024, 100 * 1024 * 1024),
            'destination': random.choice(['cloud_storage', 'external_server', 'local_drive', 'network_share']),
            'transfer_speed_mbps': random.uniform(1, 100),
            'encryption_used': random.choice([True, False]),
            'transfer_method': random.choice(['web_upload', 'ftp', 'sftp', 'cloud_sync'])
        }
    
    def _generate_database_activity(self, user: Dict) -> Dict:
        """Generate database query activity details"""
        databases = ['customer_db', 'financial_db', 'hr_db', 'inventory_db', 'analytics_db']
        
        # Users typically access databases relevant to their department
        dept_databases = {
            'IT': ['customer_db', 'analytics_db', 'inventory_db'],
            'Finance': ['financial_db', 'customer_db'],
            'HR': ['hr_db'],
            'Sales': ['customer_db', 'analytics_db'],
            'Marketing': ['customer_db', 'analytics_db'],
            'Operations': ['inventory_db', 'customer_db'],
            'Legal': ['customer_db', 'hr_db']
        }
        
        dept = user.get('department', 'IT')
        typical_dbs = dept_databases.get(dept, databases)
        
        return {
            'database_name': random.choice(typical_dbs),
            'query_type': random.choice(['SELECT', 'INSERT', 'UPDATE', 'DELETE']),
            'rows_affected': random.randint(1, 1000),  # Normal queries
            'execution_time_ms': random.randint(10, 5000),
            'tables_accessed': random.randint(1, 5),
            'sensitive_data_accessed': random.choice([True, False])
        }
    
    def _generate_system_activity(self, user: Dict) -> Dict:
        """Generate system command activity details"""
        # Separate normal vs privileged commands
        normal_commands = ['ls', 'cd', 'cp', 'mv', 'ps', 'top', 'netstat', 'ping', 'wget', 'curl']
        privileged_commands = ['sudo', 'systemctl', 'chmod', 'chown', 'rm', 'ssh', 'scp']
        
        # High-privilege users can use privileged commands
        if user.get('is_high_privilege', False) and random.random() < 0.3:
            command = random.choice(privileged_commands)
            privilege = random.choice(['admin', 'root'])
        else:
            command = random.choice(normal_commands)
            privilege = 'user'
        
        return {
            'command': command,
            'arguments': f"--{fake.word()} {fake.file_path()}",
            'exit_code': random.choice([0, 0, 0, 1, 2]),  # Mostly successful
            'execution_time_ms': random.randint(100, 10000),
            'privilege_level': privilege,
            'output_size_bytes': random.randint(0, 1024 * 1024)
        }
    
    def _generate_application_activity(self, user: Dict) -> Dict:
        """Generate application launch activity details"""
        applications = [
            'Microsoft Word', 'Excel', 'PowerPoint', 'Outlook', 'Chrome',
            'Firefox', 'Slack', 'Teams', 'Zoom', 'VS Code', 'IntelliJ',
            'Photoshop', 'SAP', 'Salesforce', 'QuickBooks'
        ]
        
        return {
            'application_name': random.choice(applications),
            'version': f"{random.randint(1, 15)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            'session_duration_minutes': random.randint(5, 480),
            'memory_usage_mb': random.randint(50, 2048),
            'cpu_usage_percent': random.uniform(1, 95),
            'files_opened': random.randint(0, 10)
        }
    
    def _generate_usb_activity(self, user: Dict) -> Dict:
        """Generate USB access activity details"""
        return {
            'device_type': random.choice(['flash_drive', 'external_hdd', 'smartphone', 'tablet']),
            'device_id': fake.uuid4(),
            'vendor': random.choice(['SanDisk', 'Kingston', 'Samsung', 'Apple', 'Generic']),
            'capacity_gb': random.choice([4, 8, 16, 32, 64, 128, 256, 512, 1024]),
            'files_transferred': random.randint(0, 100),
            'data_transferred_mb': random.randint(0, 1024),
            'action': random.choice(['read', 'write', 'both'])
        }
    
    def inject_anomalies(self, activities: List[Dict]) -> List[Dict]:
        """Inject realistic anomalies based on threat scenarios"""
        anomalous_activities = []
        
        # Select users for different threat scenarios
        total_users = len(self.users)
        
        # Data exfiltration anomalies
        exfil_count = max(1, int(total_users * self.threat_scenarios['data_exfiltration']))
        exfil_users = random.sample(self.users, exfil_count)
        
        # Privilege abuse anomalies
        privilege_count = max(1, int(total_users * self.threat_scenarios['privilege_abuse']))
        privilege_users = random.sample(self.users, privilege_count)
        
        # Credential compromise anomalies
        compromise_count = max(1, int(total_users * self.threat_scenarios['credential_compromise']))
        compromise_users = random.sample(self.users, compromise_count)
        
        # Generate anomalous activities
        for activities_batch in [activities[i:i+1000] for i in range(0, len(activities), 1000)]:
            # Data exfiltration patterns
            for user in exfil_users:
                if random.random() < 0.3:  # 30% chance per batch
                    anomaly = self._create_exfiltration_anomaly(user, activities_batch)
                    if anomaly:
                        anomalous_activities.append(anomaly)
            
            # Privilege abuse patterns  
            for user in privilege_users:
                if random.random() < 0.25:  # 25% chance per batch
                    anomaly = self._create_privilege_anomaly(user, activities_batch)
                    if anomaly:
                        anomalous_activities.append(anomaly)
            
            # Credential compromise patterns
            for user in compromise_users:
                if random.random() < 0.2:  # 20% chance per batch
                    anomaly = self._create_compromise_anomaly(user, activities_batch)
                    if anomaly:
                        anomalous_activities.append(anomaly)
        
        return activities + anomalous_activities
    
    def _create_exfiltration_anomaly(self, user: Dict, activities_batch: List[Dict]) -> Dict:
        """Create data exfiltration anomaly"""
        anomaly_time = fake.date_time_between(start_date='-30d', end_date='now')
        
        # Off-hours activities are more suspicious
        if anomaly_time.hour < 6 or anomaly_time.hour > 22:
            suspicion_boost = SUSPICION_BOOST_OFF_HOURS
        else:
            suspicion_boost = SUSPICION_BOOST_BUSINESS_HOURS
            
        anomaly = self._create_activity(user, 'file_download', anomaly_time)
        anomaly.update({
            'is_suspicious': True,
            'confidence_score': 0.7 + suspicion_boost,
            'total_size': random.randint(500 * 1024 * 1024, 5 * 1024 * 1024 * 1024),  # 500MB to 5GB
            'destination': 'external_server',
            'file_count': random.randint(50, 500),
            'transfer_method': 'encrypted_tunnel',
            'encryption_used': True,
            'anomaly_type': 'data_exfiltration',
            'risk_factors': ['large_transfer', 'off_hours', 'external_destination', 'encrypted']
        })
        
        return anomaly
    
    def _create_privilege_anomaly(self, user: Dict, activities_batch: List[Dict]) -> Dict:
        """Create privilege abuse anomaly (cross-department database access)"""
        anomaly_time = fake.date_time_between(start_date='-30d', end_date='now')
        
        # Select database user shouldn't normally access
        dept = user.get('department', 'IT')
        unauthorized_dbs = {
            'IT': ['hr_db', 'financial_db'],
            'Finance': ['hr_db'],
            'HR': ['financial_db'],
            'Sales': ['hr_db', 'financial_db'],
            'Marketing': ['hr_db', 'financial_db'],
            'Operations': ['hr_db', 'financial_db'],
            'Legal': ['financial_db']
        }
        
        target_db = random.choice(unauthorized_dbs.get(dept, ['hr_db']))
        
        anomaly = self._create_activity(user, 'database_query', anomaly_time)
        anomaly.update({
            'is_suspicious': True,
            'confidence_score': random.uniform(*ANOMALY_BASE_CONFIDENCE_RANGE),
            'query_type': 'SELECT',
            'rows_affected': random.randint(10000, 100000),  # Massive data access
            'tables_accessed': random.randint(10, 50),
            'sensitive_data_accessed': True,
            'database_name': target_db,
            'execution_time_ms': random.randint(5000, 30000),
            'anomaly_type': 'privilege_abuse',
            'risk_factors': ['cross_department_access', 'large_data_query', 'sensitive_data']
        })
        
        return anomaly
    
    def _create_compromise_anomaly(self, user: Dict, activities_batch: List[Dict]) -> Dict:
        """Create credential compromise anomaly (unusual login location/device)"""
        anomaly_time = fake.date_time_between(start_date='-30d', end_date='now')
        
        # Login from unusual location/device
        anomaly = self._create_activity(user, 'login', anomaly_time)
        anomaly.update({
            'is_suspicious': True,
            'confidence_score': random.uniform(0.5, 0.8),
            'source_ip': fake.ipv4(),  # External IP
            'device_info': f"Unknown_Device_{random.randint(1000, 9999)}",
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',  # Different OS
            'location': fake.country(),
            'login_attempts': random.randint(3, 10),
            'success': True,
            'anomaly_type': 'credential_compromise',
            'risk_factors': ['unusual_location', 'new_device', 'multiple_attempts', 'suspicious_os']
        })
        
        return anomaly
    
    def save_to_csv(self, activities: List[Dict], filename: str):
        """Save activities to CSV file"""
        df = pd.DataFrame(activities)
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Convert timestamp to string for CSV compatibility
        if 'timestamp' in df.columns:
            # Check if timestamp is datetime object
            if pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(df['timestamp'].iloc[0], datetime):
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        df.to_csv(filename, index=False)
        print(f"✅ Saved {len(activities)} activities to {filename}")
    
    def generate_complete_dataset(self) -> Tuple[List[Dict], List[Dict]]:
        """Generate complete dataset with normal and anomalous activities"""
        print("\n" + "="*60)
        print("IGNISYL Synthetic Data Generation")
        print("="*60 + "\n")
        
        print("🚀 Generating user profiles...")
        self.generate_user_profiles()
        print(f"   Created {len(self.users)} user profiles")
        
        print("\n📊 Generating normal activities...")
        start_date = datetime.now() - timedelta(days=self.num_days)
        end_date = datetime.now()
        
        normal_activities = self.generate_normal_activities(start_date, end_date)
        print(f"   Generated {len(normal_activities)} normal activities")
        
        print("\n⚠️ Injecting anomalies...")
        all_activities = self.inject_anomalies(normal_activities)
        
        # Separate normal and anomalous activities
        normal = [a for a in all_activities if not a.get('is_suspicious', False)]
        anomalous = [a for a in all_activities if a.get('is_suspicious', False)]
        
        print(f"   Injected {len(anomalous)} anomalous activities")
        
        print(f"\n📈 Dataset Summary:")
        print(f"   - Normal activities: {len(normal)} ({len(normal)/len(all_activities)*100:.1f}%)")
        print(f"   - Anomalous activities: {len(anomalous)} ({len(anomalous)/len(all_activities)*100:.1f}%)")
        print(f"   - Total: {len(all_activities)} activities")
        
        return normal, anomalous

def main():
    """Main function to generate synthetic dataset"""
    print("\n" + "="*60)
    print("IGNISYL Synthetic Data Generator")
    print("="*60)
    
    # Initialize generator
    generator = BehavioralDataGenerator(num_users=50, num_days=30)
    
    # Generate complete dataset
    normal_activities, anomalous_activities = generator.generate_complete_dataset()
    
    # Prepare data directory using cross-platform path joining
    data_dir = os.path.join(settings.DATA_PATH, "synthetic")
    os.makedirs(data_dir, exist_ok=True)
    
    print("\n💾 Saving datasets...")
    
    # Save user profiles
    users_df = pd.DataFrame(generator.users)
    users_file = os.path.join(data_dir, "user_profiles.csv")
    users_df.to_csv(users_file, index=False)
    print(f"   User profiles: {users_file}")
    
    # Save activities
    normal_file = os.path.join(data_dir, "normal_activities.csv")
    anomalous_file = os.path.join(data_dir, "anomalous_activities.csv")
    combined_file = os.path.join(data_dir, "combined_activities.csv")
    
    generator.save_to_csv(normal_activities, normal_file)
    generator.save_to_csv(anomalous_activities, anomalous_file)
    
    # Combine all activities for training
    all_activities = normal_activities + anomalous_activities
    generator.save_to_csv(all_activities, combined_file)
    
    # Generate detailed statistics
    print("\n" + "="*60)
    print("📊 Dataset Statistics")
    print("="*60)
    
    print(f"\n👥 Users: {len(generator.users)} total")
    
    # Department breakdown
    dept_counts = {}
    for user in generator.users:
        dept = user['department']
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
    
    print(f"\n📋 Users by Department:")
    for dept, count in sorted(dept_counts.items()):
        print(f"   {dept:15} {count:3} users ({count/len(generator.users)*100:5.1f}%)")
    
    # Activity type breakdown
    activity_counts = {}
    for activity in all_activities:
        act_type = activity['activity_type']
        activity_counts[act_type] = activity_counts.get(act_type, 0) + 1
    
    print(f"\n📂 Activities by Type:")
    for act_type, count in sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {act_type:20} {count:6} activities ({count/len(all_activities)*100:5.1f}%)")
    
    # Anomaly breakdown
    anomaly_types = {}
    for activity in anomalous_activities:
        anom_type = activity.get('anomaly_type', 'unknown')
        anomaly_types[anom_type] = anomaly_types.get(anom_type, 0) + 1
    
    if anomaly_types:
        print(f"\n⚠️ Anomalies by Type:")
        for anom_type, count in sorted(anomaly_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   {anom_type:25} {count:4} anomalies ({count/len(anomalous_activities)*100:5.1f}%)")
    
    print("\n" + "="*60)
    print("✅ Dataset Generation Complete!")
    print("="*60)
    print(f"\n📁 Files saved to: {data_dir}")
    print("🚀 Ready for ML model training\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during data generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)