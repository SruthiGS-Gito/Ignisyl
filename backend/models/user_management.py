"""
User Management System for IGNISYL
Handles user operations using the main database
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging
import hashlib

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from config.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserManager:
    """Manages users in IGNISYL system"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize UserManager
        
        Args:
            db_path: Path to database file (uses settings.DATA_PATH/ignisyl.db if None)
        """
        if db_path is None:
            os.makedirs(settings.DATA_PATH, exist_ok=True)
            self.db_path = os.path.join(settings.DATA_PATH, "ignisyl.db")
        else:
            self.db_path = db_path
        
        self._ensure_users_table()
    
    def _ensure_users_table(self):
        """Ensure users table exists (should be created by database.py)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if users table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='users'
                """)
                
                if cursor.fetchone() is None:
                    # Table doesn't exist, create it
                    logger.warning("Users table not found, creating it...")
                    cursor.execute("""
                        CREATE TABLE users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            password_hash TEXT,
                            full_name TEXT,
                            department TEXT,
                            role TEXT,
                            seniority_level TEXT,
                            is_active INTEGER DEFAULT 1,
                            risk_score REAL DEFAULT 0.0,
                            total_threats INTEGER DEFAULT 0,
                            last_login TEXT,
                            last_activity TEXT,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()
                    logger.info("✅ Users table created")
                
        except Exception as e:
            logger.error(f"❌ Failed to ensure users table: {e}")
            raise
    
    def register_user(self, username: str, email: str, full_name: str, 
                     department: str, role: str, password: str = "demo123",
                     seniority_level: str = "Mid") -> Dict:
        """
        Register a new user
        
        Args:
            username: Unique username
            email: User email
            full_name: Full name
            department: Department name
            role: Job role
            password: Password (default: demo123)
            seniority_level: Seniority level
            
        Returns:
            Dict with success status and user info
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Hash password
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                cursor.execute("""
                    INSERT INTO users (
                        username, email, password_hash, full_name, 
                        department, role, seniority_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (username, email, password_hash, full_name, department, role, seniority_level))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"✅ User registered: {full_name} (ID: {user_id})")
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "message": f"User {full_name} registered successfully"
                }
                
        except sqlite3.IntegrityError as e:
            logger.warning(f"User registration failed: {e}")
            return {
                "success": False,
                "message": "Username or email already exists"
            }
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def get_user(self, user_id: Optional[int] = None, username: Optional[str] = None) -> Optional[Dict]:
        """
        Get user by ID or username
        
        Args:
            user_id: User ID
            username: Username
            
        Returns:
            User dict or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if user_id:
                    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                elif username:
                    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                else:
                    return None
                
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get user: {e}")
            return None
    
    def get_all_users(self) -> List[Dict]:
        """
        Get all active users
        
        Returns:
            List of user dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM users 
                    WHERE is_active = 1 
                    ORDER BY last_activity DESC NULLS LAST
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Failed to get users: {e}")
            return []
    
    def update_user_activity(self, user_id: int, risk_score: Optional[float] = None) -> bool:
        """
        Update user's last activity and optionally risk score
        
        Args:
            user_id: User ID
            risk_score: New risk score (optional)
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                
                if risk_score is not None:
                    cursor.execute("""
                        UPDATE users 
                        SET last_activity = ?, 
                            risk_score = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (now, risk_score, now, user_id))
                else:
                    cursor.execute("""
                        UPDATE users 
                        SET last_activity = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (now, now, user_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to update user activity: {e}")
            return False
    
    def update_user(self, user_id: int, updates: Dict) -> bool:
        """
        Update user fields
        
        Args:
            user_id: User ID
            updates: Dict of fields to update
            
        Returns:
            True if successful
        """
        try:
            # Build UPDATE query dynamically
            allowed_fields = [
                'email', 'full_name', 'department', 'role', 
                'seniority_level', 'is_active', 'risk_score'
            ]
            
            update_fields = []
            values = []
            
            for field, value in updates.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                return False
            
            # Add updated_at
            update_fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"❌ Failed to update user: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """
        Soft delete user (set is_active = 0)
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users 
                    SET is_active = 0, 
                        updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), user_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"❌ Failed to delete user: {e}")
            return False
    
    def increment_threat_count(self, user_id: int) -> bool:
        """
        Increment user's threat count
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users 
                    SET total_threats = COALESCE(total_threats, 0) + 1,
                        last_activity = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), datetime.now().isoformat(), user_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"❌ Failed to increment threat count: {e}")
            return False
    
    def get_active_users_count(self, minutes: int = 10) -> int:
        """
        Get count of users active in last N minutes
        
        Args:
            minutes: Time window in minutes
            
        Returns:
            Count of active users
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                time_threshold = (datetime.now() - timedelta(minutes=minutes)).isoformat()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE is_active = 1 
                    AND last_activity >= ?
                """, (time_threshold,))
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"❌ Failed to get active users count: {e}")
            return 0
    
    def get_high_risk_users(self, threshold: float = 70.0, limit: int = 10) -> List[Dict]:
        """
        Get users with high risk scores
        
        Args:
            threshold: Risk score threshold
            limit: Max number of users to return
            
        Returns:
            List of high-risk user dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM users 
                    WHERE is_active = 1 
                    AND risk_score >= ?
                    ORDER BY risk_score DESC
                    LIMIT ?
                """, (threshold, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"❌ Failed to get high-risk users: {e}")
            return []
    
    def get_user_stats(self) -> Dict:
        """
        Get user statistics
        
        Returns:
            Dictionary with statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total users
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
                stats['total_users'] = cursor.fetchone()[0]
                
                # High risk users
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1 AND risk_score >= 70")
                stats['high_risk_users'] = cursor.fetchone()[0]
                
                # Users with threats
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1 AND total_threats > 0")
                stats['users_with_threats'] = cursor.fetchone()[0]
                
                # Active in last 10 minutes
                stats['recently_active'] = self.get_active_users_count(10)
                
                # Average risk score
                cursor.execute("SELECT AVG(risk_score) FROM users WHERE is_active = 1")
                avg_risk = cursor.fetchone()[0]
                stats['average_risk_score'] = round(avg_risk, 2) if avg_risk else 0.0
                
                # Department breakdown
                cursor.execute("""
                    SELECT department, COUNT(*) as count
                    FROM users
                    WHERE is_active = 1
                    GROUP BY department
                """)
                
                stats['by_department'] = {row[0]: row[1] for row in cursor.fetchall()}
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Failed to get user stats: {e}")
            return {}

# Global user manager instance
try:
    user_manager = UserManager()
except Exception as e:
    logger.error(f"Failed to initialize user manager: {e}")
    user_manager = None

def main():
    """Test user management functions"""
    print("\n" + "="*60)
    print("IGNISYL User Management Test")
    print("="*60 + "\n")
    
    um = UserManager()
    
    # Get all users
    users = um.get_all_users()
    print(f"📊 Total users: {len(users)}")
    
    # Get stats
    stats = um.get_user_stats()
    print(f"\n📈 User Statistics:")
    for key, value in stats.items():
        if key != 'by_department':
            print(f"   {key}: {value}")
    
    print("\n✅ User management test complete!")

if __name__ == "__main__":
    main()