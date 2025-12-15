"""Example usage of the database abstraction layer"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.db_factory import DatabaseFactory
from backend.config.database_config import get_config


def example_basic_operations():
    """Example: Basic CRUD operations"""
    print("\n" + "="*60)
    print("Example 1: Basic CRUD Operations")
    print("="*60)

    # Get database connection
    config = get_config('development')  # Uses SQLite by default
    db = DatabaseFactory.get_database(config)

    try:
        # CREATE - Insert a new user
        print("\n1️⃣ INSERT Operation:")
        db.execute_query(
            "INSERT INTO users (username, email, full_name, department, role) VALUES (?, ?, ?, ?, ?)",
            ('demo.user', 'demo@example.com', 'Demo User', 'Engineering', 'Developer')
        )
        print("   ✅ User created successfully")

        # READ - Fetch the user
        print("\n2️⃣ SELECT Operation:")
        user = db.fetch_one(
            "SELECT username, email, full_name FROM users WHERE username = ?",
            ('demo.user',)
        )
        print(f"   Found user: {user}")

        # UPDATE - Modify the user
        print("\n3️⃣ UPDATE Operation:")
        db.execute_query(
            "UPDATE users SET department = ? WHERE username = ?",
            ('Security', 'demo.user')
        )
        print("   ✅ User updated successfully")

        # Verify update
        user = db.fetch_one(
            "SELECT username, department FROM users WHERE username = ?",
            ('demo.user',)
        )
        print(f"   Updated user: {user}")

        # DELETE - Remove the user
        print("\n4️⃣ DELETE Operation:")
        db.execute_query(
            "DELETE FROM users WHERE username = ?",
            ('demo.user',)
        )
        print("   ✅ User deleted successfully")

    finally:
        db.close()


def example_batch_operations():
    """Example: Batch insert operations"""
    print("\n" + "="*60)
    print("Example 2: Batch Operations")
    print("="*60)

    config = get_config('development')
    db = DatabaseFactory.get_database(config)

    try:
        # Batch insert multiple users
        print("\n📦 Batch inserting 5 users...")
        users_data = [
            ('alice.johnson', 'alice@example.com', 'Alice Johnson', 'HR', 'Manager'),
            ('bob.smith', 'bob@example.com', 'Bob Smith', 'Finance', 'Analyst'),
            ('charlie.brown', 'charlie@example.com', 'Charlie Brown', 'IT', 'Admin'),
            ('diana.prince', 'diana@example.com', 'Diana Prince', 'Security', 'Officer'),
            ('eve.martinez', 'eve@example.com', 'Eve Martinez', 'Sales', 'Representative')
        ]

        db.execute_many(
            "INSERT INTO users (username, email, full_name, department, role) VALUES (?, ?, ?, ?, ?)",
            users_data
        )
        print("   ✅ All users inserted successfully")

        # Fetch all users
        print("\n📋 Fetching all users:")
        all_users = db.fetch_all("SELECT username, full_name, department FROM users")
        for idx, user in enumerate(all_users, 1):
            print(f"   {idx}. {user[1]} ({user[0]}) - {user[2]}")

        # Cleanup
        print("\n🧹 Cleaning up...")
        for username, _, _, _, _ in users_data:
            db.execute_query("DELETE FROM users WHERE username = ?", (username,))
        print("   ✅ Cleanup complete")

    finally:
        db.close()


def example_transactions():
    """Example: Transaction management"""
    print("\n" + "="*60)
    print("Example 3: Transaction Management")
    print("="*60)

    config = get_config('development')
    db = DatabaseFactory.get_database(config)

    try:
        print("\n✅ Successful transaction:")
        with db.transaction():
            db.execute_query(
                "INSERT INTO users (username, email, full_name) VALUES (?, ?, ?)",
                ('trans.user1', 'trans1@example.com', 'Transaction User 1')
            )
            db.execute_query(
                "INSERT INTO users (username, email, full_name) VALUES (?, ?, ?)",
                ('trans.user2', 'trans2@example.com', 'Transaction User 2')
            )
            print("   Both users inserted successfully")
        print("   Transaction committed")

        # Verify
        count = db.fetch_one("SELECT COUNT(*) FROM users WHERE username LIKE 'trans.%'")
        print(f"   Users created: {count[0]}")

        print("\n❌ Failed transaction (will rollback):")
        try:
            with db.transaction():
                db.execute_query(
                    "INSERT INTO users (username, email, full_name) VALUES (?, ?, ?)",
                    ('trans.user3', 'trans3@example.com', 'Transaction User 3')
                )
                print("   First insert successful")

                # This will fail (duplicate username)
                db.execute_query(
                    "INSERT INTO users (username, email, full_name) VALUES (?, ?, ?)",
                    ('trans.user1', 'trans1@example.com', 'Duplicate User')
                )
        except Exception as e:
            print(f"   ⚠️ Transaction failed: {e}")
            print("   Transaction rolled back")

        # Verify rollback
        count = db.fetch_one("SELECT COUNT(*) FROM users WHERE username LIKE 'trans.%'")
        print(f"   Users after rollback: {count[0]} (trans.user3 was not committed)")

        # Cleanup
        print("\n🧹 Cleaning up...")
        db.execute_query("DELETE FROM users WHERE username LIKE 'trans.%'")
        print("   ✅ Cleanup complete")

    finally:
        db.close()


def example_different_databases():
    """Example: Using different database types"""
    print("\n" + "="*60)
    print("Example 4: Multiple Database Types")
    print("="*60)

    # SQLite (Development)
    print("\n1️⃣ SQLite Database:")
    sqlite_config = get_config('development')
    print(f"   Config: {sqlite_config}")
    sqlite_db = DatabaseFactory.get_database(sqlite_config)
    result = sqlite_db.fetch_one("SELECT 1")
    print(f"   Connection test: {result}")
    sqlite_db.close()

    # PostgreSQL (Production) - will only work if PostgreSQL is set up
    print("\n2️⃣ PostgreSQL Database:")
    try:
        postgres_config = get_config('production')
        print(f"   Config: {postgres_config}")
        postgres_db = DatabaseFactory.get_database(postgres_config)
        result = postgres_db.fetch_one("SELECT 1")
        print(f"   Connection test: {result}")
        postgres_db.close()
        print("   ✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"   ⚠️ PostgreSQL not available: {e}")

    # MySQL (Production) - will only work if MySQL is set up
    print("\n3️⃣ MySQL Database:")
    try:
        mysql_config = get_config('production_mysql')
        print(f"   Config: {mysql_config}")
        mysql_db = DatabaseFactory.get_database(mysql_config)
        result = mysql_db.fetch_one("SELECT 1")
        print(f"   Connection test: {result}")
        mysql_db.close()
        print("   ✅ MySQL connection successful")
    except Exception as e:
        print(f"   ⚠️ MySQL not available: {e}")


def example_error_handling():
    """Example: Error handling and recovery"""
    print("\n" + "="*60)
    print("Example 5: Error Handling")
    print("="*60)

    config = get_config('development')
    db = DatabaseFactory.get_database(config)

    try:
        # Invalid query - syntax error
        print("\n1️⃣ Handling syntax error:")
        try:
            db.execute_query("INVALID SQL QUERY")
        except Exception as e:
            print(f"   ✅ Caught error: {type(e).__name__}")

        # Constraint violation - duplicate key
        print("\n2️⃣ Handling constraint violation:")
        try:
            db.execute_query(
                "INSERT INTO users (username, email, full_name) VALUES (?, ?, ?)",
                ('error.user', 'error@example.com', 'Error User')
            )
            # Try to insert duplicate
            db.execute_query(
                "INSERT INTO users (username, email, full_name) VALUES (?, ?, ?)",
                ('error.user', 'error@example.com', 'Error User')
            )
        except Exception as e:
            print(f"   ✅ Caught error: {type(e).__name__}")

        # Foreign key violation
        print("\n3️⃣ Handling foreign key violation:")
        try:
            db.execute_query(
                "INSERT INTO user_activities (user_id, activity_type) VALUES (?, ?)",
                (99999, 'test_activity')  # Non-existent user_id
            )
        except Exception as e:
            print(f"   ✅ Caught error: {type(e).__name__}")

        # Cleanup
        print("\n🧹 Cleaning up...")
        db.execute_query("DELETE FROM users WHERE username = 'error.user'")
        print("   ✅ Cleanup complete")

    finally:
        db.close()


def main():
    """Run all examples"""
    print("\n🚀 Database Abstraction Layer - Example Usage")
    print("="*60)

    examples = [
        ("Basic Operations", example_basic_operations),
        ("Batch Operations", example_batch_operations),
        ("Transactions", example_transactions),
        ("Different Databases", example_different_databases),
        ("Error Handling", example_error_handling)
    ]

    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("✅ All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
