"""
User Management System
Handles user registration and tracking for multi-user monitoring
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json
import os
from pathlib import Path

class UserManager:
    """Manages users being monitored by IGNISYL"""

    def __init__(self, db_path: str = None):
        # Use absolute path resolved from this file's location
        if db_path is None:
            # Get the backend directory (parent of models/)
            backend_dir = Path(__file__).parent.parent.resolve()
            self.db_path = str(backend_dir / "data" / "users.db")
        else:
            self.db_path = db_path

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Create users table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                password_hash TEXT,
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
        print("[OK] User database initialized")
    
    def register_user(self, username: str, full_name: str, department: str, 
                 role: str, email: str = None, password_hash: str = None) -> Dict:
        """Register a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
    
        # Generate user_id
        user_id = f"user_{username.lower().replace(' ', '_')}"
    
        try:
            cursor.execute("""
                INSERT INTO users (user_id, username, password_hash, full_name, department, role, email, registered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, password_hash, full_name, department, role, email, datetime.now().isoformat()))
            
            conn.commit()
            print(f"[OK] User registered: {full_name} ({user_id})")
            
            return {
                "success": True,
                "user_id": user_id,
                "username": username,
                "message": f"User {full_name} registered successfully"
            }
            
        except sqlite3.IntegrityError:
            print(f"[WARN] User {username} already exists")
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
                "password_hash": row[2],
                "full_name": row[3],
                "department": row[4],
                "role": row[5],
                "email": row[6],
                "registered_at": row[7],
                "last_activity": row[8],
                "total_threats": row[9],
                "current_risk_score": row[10],
                "status": row[11]
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
                "password_hash": row[2],
                "full_name": row[3],
                "department": row[4],
                "role": row[5],
                "email": row[6],
                "registered_at": row[7],
                "last_activity": row[8],
                "total_threats": row[9],
                "current_risk_score": row[10],
                "status": row[11]
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

    def increment_threat_count(self, user_id: str) -> bool:
        """
        Increment threat count for a user
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE users 
                SET total_threats = total_threats + 1,
                    last_activity = ?
                WHERE user_id = ?
            """, (datetime.now().isoformat(), user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error incrementing threat count: {e}")
            conn.close()
            return False

    def update_user_password(self, user_id: str, password_hash: str) -> bool:
        """
        Update user's password hash

        Args:
            user_id: User ID
            password_hash: New bcrypt password hash

        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE users
                SET password_hash = ?
                WHERE user_id = ?
            """, (password_hash, user_id))

            conn.commit()
            updated = cursor.rowcount > 0
            conn.close()

            if updated:
                print(f"[OK] Password updated for user: {user_id}")
            return updated
        except Exception as e:
            print(f"Error updating password: {e}")
            conn.close()
            return False

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username instead of user_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "user_id": row[0],
                "username": row[1],
                "password_hash": row[2],
                "full_name": row[3],
                "department": row[4],
                "role": row[5],
                "email": row[6],
                "registered_at": row[7],
                "last_activity": row[8],
                "total_threats": row[9],
                "current_risk_score": row[10],
                "status": row[11]
            }
        return None

    def calculate_user_risk_score(self, user_id: str, activities: List[Dict]) -> float:
        """
        Calculate risk score based on recent user activities
        Uses weighted average of recent activity risk scores with recency bias

        Args:
            user_id: User ID
            activities: List of recent activities for this user

        Returns:
            Calculated risk score (0-100)
        """
        if not activities:
            return 0.0

        # Filter activities for this user (last 24 hours most weighted)
        user_activities = [a for a in activities if a.get('user_id') == user_id]

        if not user_activities:
            return 0.0

        # Calculate weighted risk score
        total_weight = 0
        weighted_score = 0

        for i, activity in enumerate(user_activities[:20]):  # Last 20 activities max
            # More recent activities have higher weight
            weight = 1.0 / (i + 1)  # Recency weight

            # Risk level multiplier
            risk_level = activity.get('risk_level', 'LOW')
            level_multiplier = {
                'LOW': 0.5,
                'MEDIUM': 1.0,
                'HIGH': 1.5,
                'CRITICAL': 2.0
            }.get(risk_level, 1.0)

            risk_score = activity.get('risk_score', 0)
            weighted_score += risk_score * weight * level_multiplier
            total_weight += weight

        # Normalize to 0-100 scale
        if total_weight > 0:
            base_score = weighted_score / total_weight
        else:
            base_score = 0

        # Apply threat count modifier
        user = self.get_user(user_id)
        if user:
            threat_modifier = min(user.get('total_threats', 0) * 2, 20)  # Max 20 point addition
            final_score = min(100, base_score + threat_modifier)
        else:
            final_score = base_score

        return round(final_score, 1)

    def recalculate_all_risk_scores(self, all_activities: List[Dict]) -> Dict:
        """
        Recalculate risk scores for all users based on their activities

        Args:
            all_activities: List of all recent activities

        Returns:
            Dictionary mapping user_id to their new risk score
        """
        users = self.get_all_users()
        scores = {}

        for user in users:
            user_id = user['user_id']
            new_score = self.calculate_user_risk_score(user_id, all_activities)

            # Update the user's risk score in database
            self.update_user_activity(user_id, new_score)
            scores[user_id] = new_score

        return scores


    def update_user_status(self, user_id: str, status: str, reason: str = None) -> bool:
        """Update user's status (active, blocked, restricted)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET status = ?, last_activity = ? WHERE user_id = ?",
                          (status, datetime.now().isoformat(), user_id))
            conn.commit()
            updated = cursor.rowcount > 0
            conn.close()
            if updated:
                print(f"[STATUS] User {user_id} status changed to: {status}")
            return updated
        except Exception as e:
            print(f"Error updating user status: {e}")
            conn.close()
            return False

    def block_user(self, user_id: str, reason: str) -> bool:
        """Block a user due to security threat"""
        return self.update_user_status(user_id, 'blocked', reason)

    def restrict_user(self, user_id: str, reason: str) -> bool:
        """Restrict a user's access"""
        return self.update_user_status(user_id, 'restricted', reason)

    def unblock_user(self, user_id: str) -> bool:
        """Unblock a user"""
        return self.update_user_status(user_id, 'active', 'Manual unblock')

    def get_blocked_users(self):
        """Get all blocked users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE status = 'blocked'")
        rows = cursor.fetchall()
        conn.close()
        return [{"user_id": r[0], "username": r[1], "full_name": r[3], "status": r[11], "current_risk_score": r[10]} for r in rows]


# Global user manager instance
user_manager = UserManager()
