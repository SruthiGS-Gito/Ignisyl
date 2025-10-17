"""
User Management System
Handles user registration and tracking for multi-user monitoring
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json

class UserManager:
    """Manages users being monitored by IGNISYL"""
    
    def __init__(self, db_path: str = "data/users.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create users table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                full_name TEXT NOT NULL,
                department TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                registered_at TEXT NOT NULL,
                last_activity TEXT,
                total_threats INTEGER DEFAULT 0,
                current_risk_score REAL DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ User database initialized")
    
    def register_user(self, username: str, full_name: str, department: str, 
                     role: str, email: str = None) -> Dict:
        """Register a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate user_id
        user_id = f"user_{username.lower().replace(' ', '_')}"
        
        try:
            cursor.execute("""
                INSERT INTO users (user_id, username, full_name, department, role, email, registered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, full_name, department, role, email, datetime.now().isoformat()))
            
            conn.commit()
            print(f"✅ User registered: {full_name} ({user_id})")
            
            return {
                "success": True,
                "user_id": user_id,
                "username": username,
                "message": f"User {full_name} registered successfully"
            }
            
        except sqlite3.IntegrityError:
            print(f"⚠️ User {username} already exists")
            return {
                "success": False,
                "message": "User already exists"
            }
        finally:
            conn.close()
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "user_id": row[0],
                "username": row[1],
                "full_name": row[2],
                "department": row[3],
                "role": row[4],
                "email": row[5],
                "registered_at": row[6],
                "last_activity": row[7],
                "total_threats": row[8],
                "current_risk_score": row[9],
                "status": row[10]
            }
        return None
    
    def get_all_users(self) -> List[Dict]:
        """Get all registered users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE status = 'active' ORDER BY last_activity DESC")
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                "user_id": row[0],
                "username": row[1],
                "full_name": row[2],
                "department": row[3],
                "role": row[4],
                "email": row[5],
                "registered_at": row[6],
                "last_activity": row[7],
                "total_threats": row[8],
                "current_risk_score": row[9],
                "status": row[10]
            })
        
        return users
    
    def update_user_activity(self, user_id: str, risk_score: float = None):
        """Update user's last activity and risk score"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if risk_score is not None:
            cursor.execute("""
                UPDATE users 
                SET last_activity = ?, current_risk_score = ?
                WHERE user_id = ?
            """, (datetime.now().isoformat(), risk_score, user_id))
        else:
            cursor.execute("""
                UPDATE users 
                SET last_activity = ?
                WHERE user_id = ?
            """, (datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
    
    def increment_threat_count(self, user_id: str):
        """Increment user's threat counter"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET total_threats = total_threats + 1
            WHERE user_id = ?
        """, (user_id,))
        
        conn.commit()
        conn.close()
    
    def get_active_users_count(self) -> int:
        """Get count of users active in last 10 minutes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users active in last 10 minutes
        ten_mins_ago = datetime.now().timestamp() - 600
        
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE status = 'active' AND last_activity IS NOT NULL
        """)
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count

# Global user manager instance
user_manager = UserManager()