"""Test script for database abstraction layer"""
import sys
import os
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import traceback


def test_imports():
    """Test 1: Import DatabaseFactory and related modules"""
    print("\n" + "="*70)
    print("TEST 1: Import DatabaseFactory and Related Modules")
    print("="*70)

    try:
        from backend.database.db_factory import (
            DatabaseFactory,
            DatabaseConnection,
            SQLiteConnection,
            PostgreSQLConnection,
            MySQLConnection
        )
        print("✅ Successfully imported DatabaseFactory")
        print("✅ Successfully imported DatabaseConnection")
        print("✅ Successfully imported SQLiteConnection")
        print("✅ Successfully imported PostgreSQLConnection")
        print("✅ Successfully imported MySQLConnection")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False


def test_config():
    """Test 2: Import and verify database configuration"""
    print("\n" + "="*70)
    print("TEST 2: Import and Verify Database Configuration")
    print("="*70)

    try:
        from backend.config.database_config import DATABASE_CONFIG, get_config
        print("✅ Successfully imported database configuration")

        # Verify development config exists
        dev_config = get_config('development')
        print(f"✅ Development config loaded: {dev_config['type']}")

        # List all available environments
        print(f"✅ Available environments: {list(DATABASE_CONFIG.keys())}")

        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        traceback.print_exc()
        return False


def test_sqlite_connection():
    """Test 3: Test SQLite connection in development mode"""
    print("\n" + "="*70)
    print("TEST 3: SQLite Connection (Development Mode)")
    print("="*70)

    try:
        from backend.database.db_factory import DatabaseFactory
        from backend.config.database_config import get_config

        # Get development configuration (SQLite)
        config = get_config('development')
        print(f"Config: {config}")

        # Create database connection
        db = DatabaseFactory.get_database(config)
        print("✅ Database connection created")

        # Test simple query
        result = db.fetch_one("SELECT 1 as test")
        print(f"✅ Test query executed: {result}")

        # Close connection
        db.close()
        print("✅ Connection closed successfully")

        return True
    except Exception as e:
        print(f"❌ SQLite connection test failed: {e}")
        traceback.print_exc()
        return False


def test_crud_operations():
    """Test 4: Test basic CRUD operations"""
    print("\n" + "="*70)
    print("TEST 4: Basic CRUD Operations")
    print("="*70)

    try:
        from backend.database.db_factory import DatabaseFactory
        from backend.config.database_config import get_config

        # Use testing environment (in-memory SQLite)
        config = get_config('testing')
        db = DatabaseFactory.get_database(config)
        print("✅ Connected to in-memory test database")

        # CREATE table
        print("\n1️⃣ CREATE Table:")
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS test_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Table created")

        # INSERT
        print("\n2️⃣ INSERT Record:")
        db.execute_query(
            "INSERT INTO test_users (username, email) VALUES (?, ?)",
            ('test_user', 'test@example.com')
        )
        print("   ✅ Record inserted")

        # SELECT
        print("\n3️⃣ SELECT Record:")
        user = db.fetch_one("SELECT * FROM test_users WHERE username = ?", ('test_user',))
        print(f"   ✅ Record retrieved: {user}")

        # UPDATE
        print("\n4️⃣ UPDATE Record:")
        db.execute_query(
            "UPDATE test_users SET email = ? WHERE username = ?",
            ('updated@example.com', 'test_user')
        )
        updated_user = db.fetch_one("SELECT email FROM test_users WHERE username = ?", ('test_user',))
        print(f"   ✅ Record updated: {updated_user}")

        # DELETE
        print("\n5️⃣ DELETE Record:")
        db.execute_query("DELETE FROM test_users WHERE username = ?", ('test_user',))
        deleted_user = db.fetch_one("SELECT * FROM test_users WHERE username = ?", ('test_user',))
        print(f"   ✅ Record deleted (should be None): {deleted_user}")

        # Cleanup
        db.close()
        print("\n✅ All CRUD operations completed successfully")

        return True
    except Exception as e:
        print(f"❌ CRUD operations test failed: {e}")
        traceback.print_exc()
        return False


def test_batch_operations():
    """Test 5: Test batch insert operations"""
    print("\n" + "="*70)
    print("TEST 5: Batch Operations")
    print("="*70)

    try:
        from backend.database.db_factory import DatabaseFactory
        from backend.config.database_config import get_config

        config = get_config('testing')
        db = DatabaseFactory.get_database(config)

        # Create table
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS test_batch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                value INTEGER
            )
        """)
        print("✅ Table created")

        # Batch insert
        print("\n📦 Batch inserting 5 records:")
        test_data = [
            ('record_1', 10),
            ('record_2', 20),
            ('record_3', 30),
            ('record_4', 40),
            ('record_5', 50)
        ]

        db.execute_many(
            "INSERT INTO test_batch (name, value) VALUES (?, ?)",
            test_data
        )
        print("   ✅ Batch insert completed")

        # Verify
        all_records = db.fetch_all("SELECT * FROM test_batch")
        print(f"   ✅ Retrieved {len(all_records)} records")

        db.close()
        return True
    except Exception as e:
        print(f"❌ Batch operations test failed: {e}")
        traceback.print_exc()
        return False


def test_transactions():
    """Test 6: Test transaction management"""
    print("\n" + "="*70)
    print("TEST 6: Transaction Management")
    print("="*70)

    try:
        from backend.database.db_factory import DatabaseFactory
        from backend.config.database_config import get_config

        config = get_config('testing')
        db = DatabaseFactory.get_database(config)

        # Create table
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS test_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT
            )
        """)

        # Test successful transaction
        print("\n✅ Testing successful transaction:")
        with db.transaction():
            db.execute_query(
                "INSERT INTO test_transactions (description) VALUES (?)",
                ('transaction_1',)
            )
            db.execute_query(
                "INSERT INTO test_transactions (description) VALUES (?)",
                ('transaction_2',)
            )
        print("   ✅ Transaction committed successfully")

        count = db.fetch_one("SELECT COUNT(*) FROM test_transactions")
        print(f"   ✅ Records in database: {count[0]}")

        # Test failed transaction (rollback)
        print("\n❌ Testing failed transaction (should rollback):")
        try:
            with db.transaction():
                db.execute_query(
                    "INSERT INTO test_transactions (description) VALUES (?)",
                    ('transaction_3',)
                )
                # Force an error
                raise Exception("Simulated error")
        except Exception as e:
            print(f"   ⚠️ Transaction failed as expected: {e}")

        count_after = db.fetch_one("SELECT COUNT(*) FROM test_transactions")
        print(f"   ✅ Records after rollback: {count_after[0]} (should be {count[0]})")

        if count[0] == count_after[0]:
            print("   ✅ Rollback worked correctly!")
        else:
            print("   ❌ Rollback failed!")
            return False

        db.close()
        return True
    except Exception as e:
        print(f"❌ Transaction test failed: {e}")
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test 7: Verify backward compatibility with existing code"""
    print("\n" + "="*70)
    print("TEST 7: Backward Compatibility with Existing Code")
    print("="*70)

    try:
        # Test that original database module still works
        from backend.models.database import engine, SessionLocal, Base, User
        print("✅ Successfully imported existing database models")

        # Verify engine is created
        if engine:
            print("✅ Database engine created successfully")
        else:
            print("❌ Database engine is None")
            return False

        # Verify SessionLocal works
        if SessionLocal:
            print("✅ SessionLocal created successfully")
        else:
            print("❌ SessionLocal is None")
            return False

        # Verify Base is available
        if Base:
            print("✅ Base declarative class available")
        else:
            print("❌ Base is None")
            return False

        # Verify User model exists
        if User:
            print("✅ User model available")
            print(f"   Table name: {User.__tablename__}")
        else:
            print("❌ User model is None")
            return False

        return True
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        traceback.print_exc()
        return False


def test_error_handling():
    """Test 8: Test error handling"""
    print("\n" + "="*70)
    print("TEST 8: Error Handling")
    print("="*70)

    try:
        from backend.database.db_factory import DatabaseFactory
        from backend.config.database_config import get_config

        config = get_config('testing')
        db = DatabaseFactory.get_database(config)

        # Test 1: Invalid SQL
        print("\n1️⃣ Testing invalid SQL (should handle gracefully):")
        try:
            db.execute_query("INVALID SQL SYNTAX")
            print("   ❌ Should have raised an error")
            return False
        except Exception as e:
            print(f"   ✅ Error handled correctly: {type(e).__name__}")

        # Test 2: Query on non-existent table
        print("\n2️⃣ Testing query on non-existent table:")
        try:
            db.fetch_all("SELECT * FROM non_existent_table")
            print("   ❌ Should have raised an error")
            return False
        except Exception as e:
            print(f"   ✅ Error handled correctly: {type(e).__name__}")

        db.close()
        print("\n✅ Error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and generate report"""
    print("\n" + "="*70)
    print("🚀 DATABASE ABSTRACTION LAYER - TEST SUITE")
    print("="*70)

    tests = [
        ("Import DatabaseFactory", test_imports),
        ("Database Configuration", test_config),
        ("SQLite Connection", test_sqlite_connection),
        ("CRUD Operations", test_crud_operations),
        ("Batch Operations", test_batch_operations),
        ("Transaction Management", test_transactions),
        ("Backward Compatibility", test_backward_compatibility),
        ("Error Handling", test_error_handling)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "="*70)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    print("="*70)

    if failed == 0:
        print("\n🎉 ✅ ALL TESTS PASSED! 🎉")
        print("="*70 + "\n")
        return True
    else:
        print(f"\n⚠️ {failed} TEST(S) FAILED")
        print("="*70 + "\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
