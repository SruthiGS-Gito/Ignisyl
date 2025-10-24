"""
Database Migration Script
Adds missing columns to existing users table
"""

import sqlite3
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from config.config import settings

def migrate_users_table():
    """Add missing columns to users table"""
    db_path = os.path.join(settings.DATA_PATH, "ignisyl.db")
    
    print("\n" + "="*60)
    print("Database Migration")
    print("="*60 + "\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current columns
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"Current columns: {existing_columns}\n")
        
        # Add missing columns
        columns_to_add = {
            'risk_score': 'REAL DEFAULT 0.0',
            'total_threats': 'INTEGER DEFAULT 0',
            'last_activity': 'TEXT',
            'seniority_level': 'TEXT'
        }
        
        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column" not in str(e).lower():
                        print(f"⚠️ Could not add {column_name}: {e}")
        
        conn.commit()
        
        # Verify
        cursor.execute("PRAGMA table_info(users)")
        new_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"\n📊 Updated columns: {new_columns}")
        print("\n✅ Migration complete!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_users_table()