"""
Authentication System for IGNISYL
Handles user login, session management, and access control
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
from jose import jwt
from datetime import datetime, timedelta
import hashlib
import secrets
from models.user_management import user_manager

# Security configuration
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

security = HTTPBearer()

import sqlite3
import os

class AuthManager:
    """Manages authentication and authorization"""
    
    def __init__(self):
        # Use database for persistent sessions
        self.db_path = os.path.join('data', 'sessions.db')
        self._init_session_db()
    
    def _init_session_db(self):
        """Initialize session database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_session(self, token: str, user_data: Dict):
        """Save session to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        cursor.execute('''
            INSERT OR REPLACE INTO sessions (token, user_id, username, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (token, user_data.get('user_id'), user_data.get('username'), expires_at))
        
        conn.commit()
        conn.close()
    
    def get_session(self, token: str) -> Optional[Dict]:
        """Get session from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, expires_at FROM sessions
            WHERE token = ? AND expires_at > datetime('now')
        ''', (token,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'user_id': result[0],
                'username': result[1],
                'expires_at': result[2]
            }
        return None
    
    def delete_session(self, token: str):
        """Delete session from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
        conn.commit()
        conn.close()
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(plain_password) == hashed_password
    
    def create_access_token(self, data: Dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
        # ✅ Save session to database
        self.save_session(encoded_jwt, data)
    
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
            # ✅ Also check database session
            session = self.get_session(token)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or invalid"
                )
        
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user credentials"""
        
        # Get user from database
        users = user_manager.get_all_users()
        user = next((u for u in users if u['username'] == username), None)
        
        if not user:
            return None
        
        # For demo, accept any password (in production, check hashed password)
        if not self.verify_password(password, user.get('password_hash')):
            return None

        return user

# Global instance
auth_manager = AuthManager()

# Dependency for protected routes
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    return payload
