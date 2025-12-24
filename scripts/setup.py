"""
IGNISYL Setup Script
Initializes the project environment and dependencies
"""

import os
import sys
import subprocess

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def create_directories():
    """Create necessary directories"""
    print_header("Creating Directory Structure")
    
    directories = [
        'data/honeypots',
        'data/logs',
        'data/models',
        'data/reports',
        'data/synthetic',
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}")

def check_python_version():
    """Check Python version"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ required")
        sys.exit(1)
    
    print("✅ Python version compatible")

def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Python Dependencies")
    
    print("[*] Installing requirements...")
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Dependencies installed successfully")
    else:
        print("❌ Failed to install dependencies")
        print(result.stderr)
        sys.exit(1)

def create_honeypot_files():
    """Create honeypot decoy files"""
    print_header("Creating Honeypot Files")
    
    honeypots = [
        ('data/honeypots/admin_passwords.txt', '# Admin credentials - DO NOT ACCESS'),
        ('data/honeypots/salary_data.xlsx', '# Confidential salary information'),
        ('data/honeypots/api_keys.json', '# Production API keys'),
        ('data/honeypots/database_backup.sql', '# Production database backup'),
        ('data/honeypots/confidential_report.docx', '# Confidential company report'),
    ]
    
    for filepath, content in honeypots:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Created: {filepath}")

def initialize_databases():
    """Initialize SQLite databases"""
    print_header("Initializing Databases")
    
    try:
        from backend.models.database import init_db
        init_db()
        print("✅ Databases initialized")
    except Exception as e:
        print(f"⚠️ Could not initialize databases: {e}")
        print("   (This is OK if running setup before backend is ready)")

def setup_frontend():
    """Setup frontend dependencies"""
    print_header("Setting Up Frontend")
    
    if os.path.exists('frontend/package.json'):
        print("[*] Installing npm dependencies...")
        result = subprocess.run(
            ['npm', 'install'],
            cwd='frontend',
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Frontend dependencies installed")
        else:
            print("⚠️ Could not install frontend dependencies")
            print("   Make sure Node.js and npm are installed")
    else:
        print("⚠️ frontend/package.json not found")

def print_next_steps():
    """Print next steps"""
    print_header("Setup Complete!")
    
    print("\n[*] Next Steps:")
    print("   1. Generate training data:")
    print("      python scripts/generate_data.py")
    print("\n   2. Train ML models:")
    print("      python scripts/train_models.py")
    print("\n   3. Start backend server:")
    print("      cd backend && python main.py")
    print("\n   4. Start frontend (in new terminal):")
    print("      cd frontend && npm start")
    print("\n   5. Open browser:")
    print("      http://localhost:3000")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    print_header("IGNISYL Setup Script")
    
    try:
        check_python_version()
        create_directories()
        install_dependencies()
        create_honeypot_files()
        initialize_databases()
        setup_frontend()
        print_next_steps()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
