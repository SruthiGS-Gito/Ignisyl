"""
Authentication System for IGNISYL
Enterprise-grade user authentication and session management
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
import jwt
from datetime import datetime, timedelta
import hashlib
import os

# Security configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'ignisyl_secret_key_2025_production_change_me_12345678')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

security = HTTPBearer()

class AuthManager:
    """Enterprise authentication and session management"""
    
    def __init__(self):
        self.sessions = {}
        print("🔐 Authentication Manager initialized")
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against stored hash"""
        return self.hash_password(plain_password) == hashed_password
    
    def create_access_token(self, data: Dict) -> str:
        """Generate JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
        """Authenticate user credentials against database"""
        from models.user_management import user_manager
        
        # Query database for user
        users = user_manager.get_all_users()
        user = next((u for u in users if u['username'] == username), None)
        
        if not user:
            print(f"❌ Authentication failed: User '{username}' not found")
            return None
        
        # Retrieve stored password hash
        stored_hash = user.get('password_hash')
        
        if not stored_hash:
            print(f"⚠️ Authentication failed: User '{username}' has no password configured")
            return None
        
        # Verify password
        if not self.verify_password(password, stored_hash):
            print(f"❌ Authentication failed: Invalid password for '{username}'")
            return None
        
        # Authentication successful
        print(f"✅ User authenticated: {username} (role: {user.get('role', 'User')})")
        return user
    
    def create_session(self, user_id: str, user_data: Dict) -> str:
        """Create authenticated session and return JWT token"""
        token_data = {
            "sub": user_id,
            "username": user_data.get('username'),
            "role": user_data.get('role', 'User'),
            "full_name": user_data.get('full_name', 'Unknown'),
            "department": user_data.get('department', 'Unknown'),
            "iat": datetime.utcnow().isoformat()
        }
        
        token = self.create_access_token(token_data)
        
        # Store active session
        self.sessions[user_id] = {
            "token": token,
            "user_data": user_data,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        print(f"📝 Session created for user: {user_data.get('username')}")
        return token
    
    def invalidate_session(self, user_id: str) -> bool:
        """Invalidate user session"""
        if user_id in self.sessions:
            username = self.sessions[user_id]['user_data'].get('username', user_id)
            del self.sessions[user_id]
            print(f"🔓 Session invalidated for user: {username}")
            return True
        return False
    
    def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)
    
    def get_session_info(self, user_id: str) -> Optional[Dict]:
        """Retrieve session information"""
        return self.sessions.get(user_id)
    
    def update_last_activity(self, user_id: str):
        """Update session activity timestamp"""
        if user_id in self.sessions:
            self.sessions[user_id]['last_activity'] = datetime.utcnow().isoformat()
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions"""
        current_time = datetime.utcnow()
        expired = []
        
        for user_id, session_data in self.sessions.items():
            try:
                created_at = datetime.fromisoformat(session_data['created_at'])
                age_minutes = (current_time - created_at).total_seconds() / 60
                
                if age_minutes > ACCESS_TOKEN_EXPIRE_MINUTES:
                    expired.append(user_id)
            except Exception as e:
                print(f"Error checking session: {e}")
                expired.append(user_id)
        
        for user_id in expired:
            username = self.sessions[user_id]['user_data'].get('username', user_id)
            del self.sessions[user_id]
            print(f"🧹 Expired session cleaned: {username}")
        
        return len(expired)

# Global authentication manager
auth_manager = AuthManager()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify and return authenticated user"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    
    user_id = payload.get('sub')
    if user_id and user_id in auth_manager.sessions:
        auth_manager.update_last_activity(user_id)
        return auth_manager.sessions[user_id]['user_data']
    
    return payload

# Admin authorization dependency
async def get_admin_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Verify administrative privileges"""
    role = current_user.get('role', '').lower()
    username = current_user.get('username', '').lower()
    
    is_admin = (
        'admin' in role or 
        'administrator' in role or 
        'manager' in role or 
        username == 'admin'
    )
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required"
        )
    
    return current_user

# Optional authentication dependency
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict]:
    """Return user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None