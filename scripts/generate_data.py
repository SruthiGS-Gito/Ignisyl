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

def generate_activity(user, is_malicious=False):
    """Generate a single activity"""
    
    if is_malicious:
        # High-risk malicious activities
        activity_type = random.choice(['honeypot_access', 'privilege_escalation', 'data_transfer', 'usb_device'])
        risk_range = ACTIVITY_TYPES[activity_type]
        base_risk = random.uniform(risk_range['min_risk'], risk_range['max_risk'])
        
        # Add anomaly factors
        hour = random.choice([0, 1, 2, 3, 4, 5, 22, 23])  # Odd hours
        is_weekend = random.choice([True, True, False])
        bytes_transferred = random.randint(500_000_000, 5_000_000_000)  # Large transfer
        
    else:
        # Normal activities
        activity_type = random.choice(['file_access', 'network_access', 'login'])
        risk_range = ACTIVITY_TYPES[activity_type]
        base_risk = random.uniform(risk_range['min_risk'], risk_range['max_risk'] * 0.5)
        
        # Normal working hours
        hour = random.randint(8, 18)
        is_weekend = False
        bytes_transferred = random.randint(1_000, 50_000_000)
    
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
        'source_ip': fake.ipv4_private(),
        'bytes_transferred': bytes_transferred,
        'file_path': random.choice(FILE_TYPES) if 'file' in activity_type else None,
        'destination_ip': fake.ipv4() if 'network' in activity_type else None,
        'is_malicious': is_malicious,
        'base_risk_score': round(base_risk, 2)
    }
    
    return activity

def generate_dataset(num_users=50, activities_per_user=100, malicious_ratio=0.1):
    """Generate complete dataset"""
    
    print(f"🔄 Generating dataset...")
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
    
    print(f"✅ Generated {len(all_activities)} activities")
    
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
    print(f"💾 Saved users to {users_file}")
    
    # Save activities
    activities_file = os.path.join(output_dir, 'activities.json')
    with open(activities_file, 'w') as f:
        json.dump(activities, f, indent=2)
    print(f"💾 Saved activities to {activities_file}")
    
    # Save training data (features only)
    training_data = []
    for activity in activities:
        training_data.append({
            'hour': activity['hour'],
            'day_of_week': activity['day_of_week'],
            'is_weekend': activity['is_weekend'],
            'bytes_transferred': activity['bytes_transferred'],
            'activity_type': activity['activity_type'],
            'is_malicious': activity['is_malicious']
        })
    
    training_file = os.path.join(output_dir, 'training_data.json')
    with open(training_file, 'w') as f:
        json.dump(training_data, f, indent=2)
    print(f"💾 Saved training data to {training_file}")

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
    
    print("\n✅ Data generation complete!")
    print("=" * 60)
