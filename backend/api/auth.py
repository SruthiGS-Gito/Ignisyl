"""
Authentication System for IGNISYL
Handles user login, session management, and access control

Security Features:
- bcrypt password hashing with salt
- JWT tokens with configurable expiration
- Persistent SECRET_KEY from environment
- Rate limiting support
"""

from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
from jose import jwt
from datetime import datetime, timedelta
import secrets
import os
import bcrypt
from models.user_management import user_manager

# Load SECRET_KEY from environment or generate persistent one
def get_secret_key() -> str:
    """Get or create a persistent SECRET_KEY"""
    # First try environment variable
    key = os.environ.get('SECRET_KEY')
    if key and key != 'change-this-secret-key-in-production':
        return key

    # Try loading from config
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from config.config import settings
        if hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY != 'ignisyl-secret-key-change-in-production':
            return settings.SECRET_KEY
    except:
        pass

    # Generate and persist a key if none exists
    key_file = os.path.join(os.path.dirname(__file__), '..', 'data', '.secret_key')
    os.makedirs(os.path.dirname(key_file), exist_ok=True)

    if os.path.exists(key_file):
        with open(key_file, 'r') as f:
            return f.read().strip()

    # Generate new key and save it
    new_key = secrets.token_urlsafe(64)
    with open(key_file, 'w') as f:
        f.write(new_key)
    print("[AUTH] Generated new persistent SECRET_KEY")
    return new_key

# Security configuration
SECRET_KEY = get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

security = HTTPBearer()

# Rate limiting configuration
RATE_LIMIT_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 300  # 5 minutes
ACCOUNT_LOCKOUT_THRESHOLD = 10  # Lock account after 10 failed attempts
ACCOUNT_LOCKOUT_DURATION = 1800  # 30 minutes lockout

import sqlite3
import os

class AuthManager:
    """Manages authentication and authorization"""

    def __init__(self):
        # Use absolute path for persistent sessions database
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.resolve()
        self.db_path = str(backend_dir / "data" / "sessions.db")

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_session_db()
    
    def _init_session_db(self):
        """Initialize session and security database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        ''')

        # Rate limiting table - tracks login attempts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 0,
                ip_address TEXT
            )
        ''')

        # Account lockouts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_lockouts (
                username TEXT PRIMARY KEY,
                locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                unlock_at TIMESTAMP NOT NULL,
                failed_attempts INTEGER DEFAULT 0,
                reason TEXT
            )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_identifier ON login_attempts(identifier)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(attempt_time)')

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

    def get_active_session_count(self) -> int:
        """Get count of currently active (non-expired) sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM sessions
            WHERE expires_at > datetime('now')
        """)
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def validate_password_complexity(self, password: str) -> dict:
        """
        Validate password meets security requirements.
        Returns dict with 'valid' bool and 'errors' list.
        """
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if len(password) > 128:
            errors.append("Password must not exceed 128 characters")

        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        # Check for common weak passwords
        weak_passwords = [
            'password', 'password123', '12345678', 'qwerty123',
            'admin123', 'letmein', 'welcome', 'monkey123'
        ]
        if password.lower() in weak_passwords:
            errors.append("Password is too common. Please choose a stronger password")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with automatic salt"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds is secure and reasonable
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt hash with detailed error handling"""
        if not hashed_password:
            print("[AUTH] VERIFY: No password hash provided")
            return False

        if not plain_password:
            print("[AUTH] VERIFY: No password provided")
            return False

        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')

            # Check if it's a valid bcrypt hash (starts with $2a$, $2b$, or $2y$)
            if not hashed_password.startswith(('$2a$', '$2b$', '$2y$')):
                print(f"[AUTH] VERIFY: Invalid hash format (not bcrypt). Hash prefix: {hashed_password[:10]}...")
                # This is likely a legacy hash - reject it and require password reset
                return False

            result = bcrypt.checkpw(password_bytes, hashed_bytes)
            if result:
                print("[AUTH] VERIFY: Password verification successful")
            else:
                print("[AUTH] VERIFY: Password verification failed - incorrect password")
            return result

        except (ValueError, TypeError) as e:
            print(f"[AUTH] VERIFY: Password verification error - {type(e).__name__}: {e}")
            return False
        except Exception as e:
            print(f"[AUTH] VERIFY: Unexpected error during password verification - {type(e).__name__}: {e}")
            return False

    def check_rate_limit(self, identifier: str, ip_address: str = None) -> bool:
        """Check if login attempt is within rate limits (database-backed)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Clean up old attempts
        cursor.execute('''
            DELETE FROM login_attempts
            WHERE attempt_time < datetime('now', '-' || ? || ' seconds')
        ''', (RATE_LIMIT_WINDOW,))

        # Count recent attempts for this identifier
        cursor.execute('''
            SELECT COUNT(*) FROM login_attempts
            WHERE identifier = ?
            AND attempt_time >= datetime('now', '-' || ? || ' seconds')
        ''', (identifier, RATE_LIMIT_WINDOW))

        count = cursor.fetchone()[0]

        if count >= RATE_LIMIT_ATTEMPTS:
            conn.close()
            return False

        # Record this attempt
        cursor.execute('''
            INSERT INTO login_attempts (identifier, ip_address)
            VALUES (?, ?)
        ''', (identifier, ip_address))

        conn.commit()
        conn.close()
        return True

    def get_rate_limit_reset(self, identifier: str) -> int:
        """Get seconds until rate limit resets (database-backed)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT MIN(attempt_time) FROM login_attempts
            WHERE identifier = ?
            AND attempt_time >= datetime('now', '-' || ? || ' seconds')
        ''', (identifier, RATE_LIMIT_WINDOW))

        result = cursor.fetchone()[0]
        conn.close()

        if not result:
            return 0

        # Calculate remaining time
        from datetime import datetime
        oldest = datetime.fromisoformat(result.replace(' ', 'T'))
        now = datetime.utcnow()
        elapsed = (now - oldest).total_seconds()
        return max(0, int(RATE_LIMIT_WINDOW - elapsed))

    def record_login_attempt(self, username: str, success: bool, ip_address: str = None):
        """Record login attempt and handle account lockout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if not success:
            # Check failed attempts count for this user
            cursor.execute('''
                SELECT COUNT(*) FROM login_attempts
                WHERE identifier LIKE ?
                AND success = 0
                AND attempt_time >= datetime('now', '-1 hour')
            ''', (f'%:{username}',))

            failed_count = cursor.fetchone()[0]

            if failed_count >= ACCOUNT_LOCKOUT_THRESHOLD:
                # Lock the account
                unlock_time = datetime.utcnow() + timedelta(seconds=ACCOUNT_LOCKOUT_DURATION)
                cursor.execute('''
                    INSERT OR REPLACE INTO account_lockouts
                    (username, unlock_at, failed_attempts, reason)
                    VALUES (?, ?, ?, ?)
                ''', (username, unlock_time.isoformat(), failed_count, 'Too many failed login attempts'))
                print(f"[AUTH] Account locked: {username} (failed attempts: {failed_count})")

        conn.commit()
        conn.close()

    def is_account_locked(self, username: str) -> dict:
        """Check if account is locked"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT locked_at, unlock_at, failed_attempts, reason
            FROM account_lockouts
            WHERE username = ?
        ''', (username,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            return {'locked': False}

        unlock_at = datetime.fromisoformat(result[1])
        if datetime.utcnow() >= unlock_at:
            # Lockout expired, remove it
            self.unlock_account(username)
            return {'locked': False}

        remaining = int((unlock_at - datetime.utcnow()).total_seconds())
        return {
            'locked': True,
            'unlock_at': result[1],
            'remaining_seconds': remaining,
            'failed_attempts': result[2],
            'reason': result[3]
        }

    def unlock_account(self, username: str):
        """Unlock a user account"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM account_lockouts WHERE username = ?', (username,))
        conn.commit()
        conn.close()
        print(f"[AUTH] Account unlocked: {username}")
    
    def create_access_token(self, data: Dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
        # [OK] Save session to database
        self.save_session(encoded_jwt, data)
    
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
            # [OK] Also check database session
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
        """Authenticate user credentials with detailed logging"""
        import logging
        logger = logging.getLogger(__name__)

        # Use dedicated username lookup (not filtered by status)
        user = user_manager.get_user_by_username(username)

        if not user:
            logger.warning(f"Authentication failed: User '{username}' not found in database")
            print(f"[AUTH] AUTH: User '{username}' not found")
            return None

        # Check if user is active
        if user.get('status') != 'active':
            logger.warning(f"Authentication failed: User '{username}' account is {user.get('status')}")
            print(f"[AUTH] AUTH: User '{username}' account is not active (status: {user.get('status')})")
            return None

        # Check if password hash exists
        password_hash = user.get('password_hash')
        if not password_hash:
            logger.warning(f"Authentication failed: User '{username}' has no password set")
            print(f"[AUTH] AUTH: User '{username}' has no password hash in database")
            return None

        # Verify password
        if not self.verify_password(password, password_hash):
            logger.warning(f"Authentication failed: Invalid password for user '{username}'")
            print(f"[AUTH] AUTH: Invalid password for user '{username}'")
            return None

        logger.info(f"Authentication successful for user '{username}'")
        print(f"[OK] AUTH: User '{username}' authenticated successfully")
        return user

# Global instance
auth_manager = AuthManager()

# Dependency for protected routes
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    return payload

# Dependency for admin-only routes
async def get_admin_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Require admin privileges for protected routes"""
    is_admin = current_user.get('is_admin', False)
    role = current_user.get('role', '').lower()

    # Check if user has admin privileges
    admin_roles = ['administrator', 'admin', 'security analyst']
    if not is_admin and role not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user

# Dependency for analyst or admin routes
async def get_analyst_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Require analyst or admin privileges"""
    role = current_user.get('role', '').lower()
    allowed_roles = ['administrator', 'admin', 'security analyst', 'analyst']

    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst privileges required"
        )

    return current_user
