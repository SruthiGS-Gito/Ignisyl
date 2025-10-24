"""
Database Models and Setup for IGNISYL
Manages user data, activities, and system operations
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict
import logging
import sys

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from config.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """Main database manager for IGNISYL"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            os.makedirs(settings.DATA_PATH, exist_ok=True)
            self.db_path = os.path.join(settings.DATA_PATH, "ignisyl.db")
        else:
            self.db_path = db_path
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Create all necessary tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
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
                
                # User activities table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        activity_type TEXT NOT NULL,
                        activity_details TEXT,
                        source_ip TEXT,
                        destination_ip TEXT,
                        user_agent TEXT,
                        device_info TEXT,
                        file_path TEXT,
                        file_size INTEGER,
                        network_bytes INTEGER,
                        protocol TEXT,
                        timestamp TEXT NOT NULL,
                        is_suspicious INTEGER DEFAULT 0,
                        confidence_score REAL DEFAULT 0.0,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                
                # Risk assessments table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS risk_assessments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        activity_id INTEGER,
                        risk_score REAL NOT NULL,
                        risk_level TEXT NOT NULL,
                        assessment_details TEXT,
                        anomaly_factors TEXT,
                        firewall_action TEXT,
                        is_false_positive INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        resolved_at TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (activity_id) REFERENCES user_activities(id)
                    )
                """)
                
                # Alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        alert_data TEXT,
                        is_acknowledged INTEGER DEFAULT 0,
                        acknowledged_by TEXT,
                        acknowledged_at TEXT,
                        is_resolved INTEGER DEFAULT 0,
                        resolved_by TEXT,
                        resolved_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                
                # System logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        log_level TEXT NOT NULL,
                        component TEXT NOT NULL,
                        event_type TEXT,
                        message TEXT NOT NULL,
                        additional_data TEXT,
                        user_id INTEGER,
                        ip_address TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                
                # ML model metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ml_model_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_name TEXT NOT NULL,
                        model_version TEXT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        training_data_size INTEGER,
                        evaluation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                        additional_metrics TEXT
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_user ON user_activities(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON user_activities(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessments_user ON risk_assessments(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
                
                conn.commit()
                logger.info(f"✅ Database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a SELECT query and return results as list of dicts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return 0

def init_sample_data(db: Database):
    """Initialize database with sample data"""
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if users already exist
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] > 0:
                logger.info("📊 Sample data already exists")
                return
            
            # Sample users with hashed password (demo123)
            import hashlib
            password_hash = hashlib.sha256("demo123".encode()).hexdigest()
            
            sample_users = [
                ("admin", "admin@ignisyl.com", password_hash, "System Administrator", "IT", "Administrator", "Executive"),
                ("john_doe", "john.doe@company.com", password_hash, "John Doe", "IT", "Software Engineer", "Senior"),
                ("jane_smith", "jane.smith@company.com", password_hash, "Jane Smith", "Finance", "Financial Analyst", "Mid"),
                ("mike_wilson", "mike.wilson@company.com", password_hash, "Mike Wilson", "HR", "HR Manager", "Senior"),
                ("sarah_johnson", "sarah.johnson@company.com", password_hash, "Sarah Johnson", "Sales", "Sales Rep", "Junior"),
                ("david_brown", "david.brown@company.com", password_hash, "David Brown", "Marketing", "Marketing Manager", "Senior"),
                ("emily_davis", "emily.davis@company.com", password_hash, "Emily Davis", "Operations", "Operations Analyst", "Mid"),
                ("robert_garcia", "robert.garcia@company.com", password_hash, "Robert Garcia", "IT", "Security Analyst", "Senior"),
                ("lisa_martinez", "lisa.martinez@company.com", password_hash, "Lisa Martinez", "Finance", "Accountant", "Mid"),
                ("james_rodriguez", "james.rodriguez@company.com", password_hash, "James Rodriguez", "Sales", "Account Manager", "Senior")
            ]
            
            cursor.executemany("""
                INSERT INTO users (username, email, password_hash, full_name, department, role, seniority_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, sample_users)
            
            conn.commit()
            logger.info(f"✅ Created {len(sample_users)} sample users")
            
            # Log system initialization
            cursor.execute("""
                INSERT INTO system_logs (log_level, component, event_type, message)
                VALUES (?, ?, ?, ?)
            """, ("INFO", "DATABASE", "INITIALIZATION", "Database initialized with sample data"))
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"❌ Failed to create sample data: {e}")
        raise

def get_database_stats(db: Database) -> Dict:
    """Get database statistics"""
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count records in each table
            tables = ['users', 'user_activities', 'risk_assessments', 'alerts', 'system_logs']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Active users
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
            stats['active_users'] = cursor.fetchone()[0]
            
            # High-risk activities
            cursor.execute("SELECT COUNT(*) FROM risk_assessments WHERE risk_level = 'HIGH'")
            stats['high_risk_assessments'] = cursor.fetchone()[0]
            
            # Unresolved alerts
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE is_resolved = 0")
            stats['unresolved_alerts'] = cursor.fetchone()[0]
            
            return stats
            
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}

# Global database instance
try:
    database = Database()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    database = None

def main():
    """Initialize database and create sample data"""
    print("\n" + "="*60)
    print("IGNISYL Database Initialization")
    print("="*60 + "\n")
    
    db = Database()
    init_sample_data(db)
    
    stats = get_database_stats(db)
    
    print("\n📊 Database Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Database initialization complete!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()