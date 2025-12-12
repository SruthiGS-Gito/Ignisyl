"""
Real-time Honeypot File Watcher
Monitors honeypot files and triggers INSTANT alerts on access
"""

import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from datetime import datetime
from pathlib import Path
from typing import Callable

class HoneypotWatcher(FileSystemEventHandler):
    """Watches honeypot files for access in real-time"""
    
    def __init__(self, honeypot_dir: str, callback: Callable, loop=None):
        super().__init__()
        self.honeypot_dir = Path(honeypot_dir)
        self.callback = callback
        self.observer = Observer()
        self.running = False
        self.loop = loop or asyncio.get_event_loop()
    
        print(f"🔍 Honeypot Watcher initialized for: {self.honeypot_dir}")
    
    def on_any_event(self, event: FileSystemEvent):
        """Triggered on ANY file system event"""
        # Ignore directory events
        if event.is_directory:
            return
        
        # Get filename
        filepath = Path(event.src_path)
        filename = filepath.name
        
        # Check if it's a honeypot file
        honeypot_files = [
            "confidential_salary_data.xlsx",
            "customer_credit_cards.csv",
            "admin_passwords.txt",
            "financial_reports_q4.pdf",
            "trade_secrets.docx"
        ]
        
        if filename in honeypot_files:
            # Determine event type
            event_type = event.event_type  # 'opened', 'modified', 'accessed', etc.
            
            # Trigger INSTANT alert
            alert_data = {
                'honeypot_file': filename,
                'filepath': str(filepath),
                'event_type': event_type,
                'accessed_at': datetime.now().isoformat(),
                'severity': 'CRITICAL',
                'description': f'🚨 HONEYPOT TRIGGERED: {event_type.upper()} on {filename}'
            }
            
            print(f"\n{'='*70}")
            print(f"🚨 CRITICAL ALERT - HONEYPOT ACCESSED!")
            print(f"{'='*70}")
            print(f"File: {filename}")
            print(f"Event: {event_type}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Path: {filepath}")
            print(f"{'='*70}\n")
            
            # Schedule callback in the event loop (thread-safe)
            asyncio.run_coroutine_threadsafe(self.callback(alert_data), self.loop)
    
    def start_watching(self):
        """Start real-time monitoring"""
        if not self.honeypot_dir.exists():
            self.honeypot_dir.mkdir(parents=True, exist_ok=True)
        
        self.observer.schedule(self, str(self.honeypot_dir), recursive=False)
        self.observer.start()
        self.running = True
        
        print(f"✅ Real-time honeypot monitoring ACTIVE")
        print(f"   Monitoring: {self.honeypot_dir}")
        print(f"   Any access will trigger INSTANT alert!")
    
    def stop_watching(self):
        """Stop monitoring"""
        if self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            print("🛑 Honeypot monitoring stopped")

# Callback function for handling alerts
async def handle_honeypot_alert(alert_data: dict):
    """Handle honeypot alert - log to DB and broadcast"""
    try:
        from models.activity_log import activity_logger
        from models.user_management import user_manager
        from api.websocket import notify_threat_detected
        
        # Get first user for demo (in production, use forensics to identify actual user)
        all_users = user_manager.get_all_users()
        if not all_users:
            return
        
        user = all_users[0]
        
        # Log to database
        activity_logger.log_activity({
            'user_id': user['user_id'],
            'username': user['username'],
            'full_name': user['full_name'],
            'activity_type': 'honeypot_access',
            'timestamp': alert_data['accessed_at'],
            'risk_score': 100,
            'risk_level': 'CRITICAL',
            'action': 'BLOCK',
            'bytes_transferred': 0,
            'file_size': 0,
            'summary': alert_data['description'],
            'details': alert_data
        })
        
        print("✅ Alert logged to database")
        
        # Broadcast to dashboard
        await notify_threat_detected({
            'user_id': user['user_id'],
            'threat_type': 'honeypot_access',
            'risk_score': 100,
            'risk_level': 'CRITICAL',
            'action': 'BLOCK',
            'honeypot_file': alert_data['honeypot_file'],
            'timestamp': alert_data['accessed_at'],
            'summary': alert_data['description']
        })
        
        print("📡 Alert broadcasted to dashboard!")
        
    except Exception as e:
        print(f"❌ Error handling honeypot alert: {e}")
        import traceback
        traceback.print_exc()

# Global watcher instance
honeypot_watcher = None

def start_honeypot_monitoring():
    """Start the real-time honeypot watcher"""
    global honeypot_watcher
    
    honeypot_dir = "data/honeypots"
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    honeypot_watcher = HoneypotWatcher(honeypot_dir, handle_honeypot_alert, loop=loop)
    honeypot_watcher.start_watching()
    
    return honeypot_watcher
