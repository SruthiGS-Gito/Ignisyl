"""
Generate Synthetic Training Data for IGNISYL
Creates realistic user activity data for ML model training
"""

import json
import random
from datetime import datetime, timedelta
from faker import Faker
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

fake = Faker()

# Activity types with their typical risk levels
ACTIVITY_TYPES = {
    'file_access': {'min_risk': 0, 'max_risk': 40},
    'network_access': {'min_risk': 10, 'max_risk': 50},
    'login': {'min_risk': 0, 'max_risk': 30},
    'data_transfer': {'min_risk': 20, 'max_risk': 70},
    'privilege_escalation': {'min_risk': 50, 'max_risk': 90},
    'usb_device': {'min_risk': 30, 'max_risk': 80},
    'honeypot_access': {'min_risk': 90, 'max_risk': 100},
}

# Departments
DEPARTMENTS = ['IT', 'Finance', 'HR', 'Sales', 'Marketing', 'Operations', 'Legal']

# File types
FILE_TYPES = [
    'financial_report.xlsx', 'employee_data.csv', 'confidential_memo.docx',
    'salary_info.xlsx', 'client_list.csv', 'source_code.py', 'database_backup.sql',
    'api_keys.txt', 'passwords.txt', 'admin_credentials.txt'
]

def generate_user():
    """Generate a synthetic user"""
    first_name = fake.first_name()
    last_name = fake.last_name()
    
    return {
        'user_id': f"{first_name.lower()}_{last_name.lower()}",
        'username': f"{first_name.lower()}.{last_name.lower()}",
        'full_name': f"{first_name} {last_name}",
        'email': f"{first_name.lower()}.{last_name.lower()}@company.com",
        'department': random.choice(DEPARTMENTS),
        'role': random.choice(['Employee', 'Developer', 'Manager', 'Administrator']),
    }

def get_file_risk(file_path):
    """Calculate risk score based on file type"""
    if not file_path:
        return 0
    
    high_risk_files = [
        'passwords.txt', 'api_keys.txt', 'database_backup.sql',
        'admin_credentials.txt', 'salary_info.xlsx', 'client_list.csv'
    ]
    
    medium_risk_files = [
        'financial_report.xlsx', 'employee_data.csv', 'confidential_memo.docx'
    ]
    
    file_name = file_path.lower() if isinstance(file_path, str) else ''
    
    for high_risk in high_risk_files:
        if high_risk in file_name:
            return 90
    
    for medium_risk in medium_risk_files:
        if medium_risk in file_name:
            return 50
    
    return 10  # Low risk

def generate_activity(user, is_malicious=False):
    """Generate a single activity"""
    
    if is_malicious:
        # Malicious activities - SUSPICIOUS but not EXTREME
        activity_type = random.choice([
            'honeypot_access', 'privilege_escalation', 
            'data_transfer', 'usb_device'
        ])
        risk_range = ACTIVITY_TYPES[activity_type]
        base_risk = random.uniform(risk_range['min_risk'], risk_range['max_risk'])
        
        # More suspicious timing (but some overlap with normal)
        hour = random.choice([
            0, 1, 2, 3, 4,  # Late night
            22, 23,         # Late evening
            12, 13, 14      # Some during lunch (realistic!)
        ])
        is_weekend = random.choice([True, True, False])
        is_business_hours = hour in range(9, 18)
        
        # Larger transfers but with overlap
        bytes_transferred = random.randint(
            50_000_000,      # 50MB min
            2_000_000_000    # 2GB max (not 5GB!)
        )
        
        # Larger files but realistic
        file_size = random.randint(
            10_000_000,      # 10MB min
            500_000_000      # 500MB max (not 1GB!)
        )
        
        # Higher confidence but not extreme
        confidence_score = random.uniform(0.5, 0.85)  # Not 0.95!
        
    else:
        # Normal activities - some legitimate large transfers
        activity_type = random.choice([
            'file_access', 'network_access', 'login'
        ])
        risk_range = ACTIVITY_TYPES[activity_type]
        base_risk = random.uniform(
            risk_range['min_risk'],
            risk_range['max_risk'] * 0.5
        )

        # Normal working hours (but some late workers!)
        # 24 weights for 24 hours (0-23)
        hour = random.choices(
            range(24),
            weights=[
                1, 1, 1, 1, 1, 1, 1, 1,  # 0-7am: rare (night/early morning)
                5, 8, 10, 10,             # 8-11am: common (morning work)
                8, 8,                     # 12-1pm: lunch
                10, 10, 8, 5,             # 2-5pm: common (afternoon work)
                3, 2,                     # 6-7pm: some late workers
                1, 1, 1, 1                # 8-11pm: rare (evening)
            ]
        )[0]
        
        is_weekend = random.random() < 0.1  # 10% weekend work
        is_business_hours = hour in range(9, 18)
        
        # Normal transfers with some large ones (reports, backups)
        if random.random() < 0.9:  # 90% small
            bytes_transferred = random.randint(1_000, 20_000_000)  # 1KB-20MB
            file_size = random.randint(1_000, 10_000_000)  # 1KB-10MB
        else:  # 10% large (legitimate reports/backups)
            bytes_transferred = random.randint(20_000_000, 200_000_000)  # 20MB-200MB
            file_size = random.randint(10_000_000, 100_000_000)  # 10MB-100MB
        
        # Lower confidence
        confidence_score = random.uniform(0.1, 0.4)
    
    # Generate timestamp
    days_ago = random.randint(0, 30)
    timestamp = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
    timestamp = timestamp.replace(hour=hour)
    
    activity = {
        'user_id': user['user_id'],
        'username': user['username'],
        'full_name': user['full_name'],
        'department': user['department'],
        'activity_type': activity_type,
        'timestamp': timestamp.isoformat(),
        'hour': hour,
        'day_of_week': timestamp.weekday(),
        'is_weekend': is_weekend,
        'is_business_hours': is_business_hours,
        'source_ip': fake.ipv4_private(),
        'bytes_transferred': bytes_transferred,
        'file_size': file_size,
        'confidence_score': confidence_score,
        'file_path': random.choice(FILE_TYPES) if 'file' in activity_type else None,
        'destination_ip': fake.ipv4() if 'network' in activity_type else None,
        'is_malicious': is_malicious,
        'base_risk_score': round(base_risk, 2)
    }
    
    activity['failed_login_count'] = random.randint(3, 10) if is_malicious else random.randint(0, 1)
    activity['access_frequency'] = random.uniform(10, 50) if is_malicious else random.uniform(1, 5)
    activity['unusual_location'] = is_malicious and random.random() > 0.5
    activity['file_type_risk'] = get_file_risk(activity['file_path'])
    activity['time_since_last'] = random.randint(1, 5) if is_malicious else random.randint(30, 300)
    
    return activity

def generate_dataset(num_users=50, activities_per_user=100, malicious_ratio=0.1):
    """Generate complete dataset"""

    print(f"Generating dataset...")
    print(f"   Users: {num_users}")
    print(f"   Activities per user: {activities_per_user}")
    print(f"   Malicious ratio: {malicious_ratio * 100}%")

    users = [generate_user() for _ in range(num_users)]

    all_activities = []
    for user in users:
        for _ in range(activities_per_user):
            is_malicious = random.random() < malicious_ratio
            activity = generate_activity(user, is_malicious)
            all_activities.append(activity)

    print(f"Generated {len(all_activities)} activities")

    # Calculate statistics
    malicious_count = sum(1 for a in all_activities if a['is_malicious'])
    print(f"   Malicious activities: {malicious_count} ({malicious_count/len(all_activities)*100:.1f}%)")
    print(f"   Normal activities: {len(all_activities) - malicious_count}")
    
    return users, all_activities

def save_dataset(users, activities, output_dir='data/synthetic'):
    """Save dataset to files"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save users
    users_file = os.path.join(output_dir, 'users.json')
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)
    print(f"Saved users to {users_file}")

    # Save activities
    activities_file = os.path.join(output_dir, 'activities.json')
    with open(activities_file, 'w') as f:
        json.dump(activities, f, indent=2)
    print(f"Saved activities to {activities_file}")
    
    # Save training data (features only)
    training_data = []
    for activity in activities:
        training_data.append({
            'hour': activity['hour'],
            'day_of_week': activity['day_of_week'],
            'file_size': activity.get('file_size', 0),
            'bytes_transferred': activity['bytes_transferred'],
            'is_weekend': activity['is_weekend'],
            'is_business_hours': activity.get('is_business_hours', False),
            'confidence_score': activity.get('confidence_score', 0.2),
            'failed_login_count': activity.get('failed_login_count', 0),           # NEW
            'access_frequency': activity.get('access_frequency', 1.0),             # NEW
            'unusual_location': int(activity.get('unusual_location', False)),      # NEW
            'file_type_risk': activity.get('file_type_risk', 0),                   # NEW
            'time_since_last': activity.get('time_since_last', 60),               # NEW
            'activity_type': activity['activity_type'],
            'is_malicious': activity['is_malicious']
        })
    
    training_file = os.path.join(output_dir, 'training_data.json')
    with open(training_file, 'w') as f:
        json.dump(training_data, f, indent=2)
    print(f"Saved training data to {training_file}")

if __name__ == '__main__':
    print("=" * 60)
    print("IGNISYL - Synthetic Data Generator")
    print("=" * 60)
    
    # Generate dataset
    users, activities = generate_dataset(
        num_users=50,
        activities_per_user=100,
        malicious_ratio=0.1
    )
    
    # Save to files
    save_dataset(users, activities)

    print("\nData generation complete!")
    print("=" * 60)
