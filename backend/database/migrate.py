"""Database migration utilities for Ignisyl"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.database.db_factory import DatabaseFactory
from backend.config.database_config import get_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables_sql(db_type: str) -> list:
    """Get SQL statements to create tables for different database types

    Args:
        db_type: Database type ('sqlite', 'postgresql', 'mysql')

    Returns:
        List of SQL CREATE TABLE statements
    """

    if db_type == 'postgresql':
        return [
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                email VARCHAR(100) UNIQUE,
                full_name VARCHAR(100),
                department VARCHAR(50),
                role VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            );
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            """,
            """
            CREATE TABLE IF NOT EXISTS user_activities (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                activity_type VARCHAR(50) NOT NULL,
                activity_details TEXT,
                source_ip VARCHAR(45),
                user_agent VARCHAR(500),
                device_info VARCHAR(200),
                file_path VARCHAR(500),
                file_size INTEGER,
                network_bytes INTEGER,
                protocol VARCHAR(20),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                is_suspicious BOOLEAN DEFAULT FALSE,
                confidence_score DOUBLE PRECISION DEFAULT 0.0
            );
            CREATE INDEX IF NOT EXISTS idx_activities_user_id ON user_activities(user_id);
            CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON user_activities(timestamp);
            """,
            """
            CREATE TABLE IF NOT EXISTS risk_assessments (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                risk_score DOUBLE PRECISION NOT NULL,
                risk_level VARCHAR(20) NOT NULL,
                assessment_details TEXT,
                anomaly_factors TEXT,
                firewall_action VARCHAR(20),
                is_false_positive BOOLEAN,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP WITH TIME ZONE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS firewall_rules (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                rule_type VARCHAR(20) NOT NULL,
                source_ip VARCHAR(45),
                destination_ip VARCHAR(45),
                port INTEGER,
                protocol VARCHAR(20),
                rule_details TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_by VARCHAR(50),
                expires_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                alert_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                alert_data TEXT,
                is_acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by VARCHAR(50),
                acknowledged_at TIMESTAMP WITH TIME ZONE,
                is_resolved BOOLEAN DEFAULT FALSE,
                resolved_by VARCHAR(50),
                resolved_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS system_logs (
                id SERIAL PRIMARY KEY,
                log_level VARCHAR(20) NOT NULL,
                component VARCHAR(50) NOT NULL,
                event_type VARCHAR(50),
                message TEXT NOT NULL,
                additional_data TEXT,
                user_id INTEGER REFERENCES users(id),
                ip_address VARCHAR(45),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS ml_model_metrics (
                id SERIAL PRIMARY KEY,
                model_name VARCHAR(100) NOT NULL,
                model_version VARCHAR(20),
                metric_name VARCHAR(50) NOT NULL,
                metric_value DOUBLE PRECISION NOT NULL,
                training_data_size INTEGER,
                evaluation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                additional_metrics TEXT
            );
            """
        ]
    elif db_type == 'mysql':
        return [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                email VARCHAR(100) UNIQUE,
                full_name VARCHAR(100),
                department VARCHAR(50),
                role VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_users_username (username),
                INDEX idx_users_email (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS user_activities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                activity_type VARCHAR(50) NOT NULL,
                activity_details TEXT,
                source_ip VARCHAR(45),
                user_agent VARCHAR(500),
                device_info VARCHAR(200),
                file_path VARCHAR(500),
                file_size INT,
                network_bytes INT,
                protocol VARCHAR(20),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_suspicious BOOLEAN DEFAULT FALSE,
                confidence_score DOUBLE DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                INDEX idx_activities_user_id (user_id),
                INDEX idx_activities_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS risk_assessments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                risk_score DOUBLE NOT NULL,
                risk_level VARCHAR(20) NOT NULL,
                assessment_details TEXT,
                anomaly_factors TEXT,
                firewall_action VARCHAR(20),
                is_false_positive BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS firewall_rules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                rule_type VARCHAR(20) NOT NULL,
                source_ip VARCHAR(45),
                destination_ip VARCHAR(45),
                port INT,
                protocol VARCHAR(20),
                rule_details TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_by VARCHAR(50),
                expires_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                alert_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                alert_data TEXT,
                is_acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by VARCHAR(50),
                acknowledged_at TIMESTAMP NULL,
                is_resolved BOOLEAN DEFAULT FALSE,
                resolved_by VARCHAR(50),
                resolved_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS system_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                log_level VARCHAR(20) NOT NULL,
                component VARCHAR(50) NOT NULL,
                event_type VARCHAR(50),
                message TEXT NOT NULL,
                additional_data TEXT,
                user_id INT,
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS ml_model_metrics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                model_name VARCHAR(100) NOT NULL,
                model_version VARCHAR(20),
                metric_name VARCHAR(50) NOT NULL,
                metric_value DOUBLE NOT NULL,
                training_data_size INT,
                evaluation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                additional_metrics TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        ]
    else:  # SQLite
        return [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                email TEXT UNIQUE,
                full_name TEXT,
                department TEXT,
                role TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            """,
            """
            CREATE TABLE IF NOT EXISTS user_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                activity_details TEXT,
                source_ip TEXT,
                user_agent TEXT,
                device_info TEXT,
                file_path TEXT,
                file_size INTEGER,
                network_bytes INTEGER,
                protocol TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_suspicious INTEGER DEFAULT 0,
                confidence_score REAL DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS idx_activities_user_id ON user_activities(user_id);
            CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON user_activities(timestamp);
            """
        ]


def migrate_database(environment: str = 'development'):
    """Run database migration for specified environment

    Args:
        environment: Environment name ('development', 'production', etc.)
    """
    logger.info(f"Starting migration for environment: {environment}")

    try:
        # Get configuration
        config = get_config(environment)
        db_type = config.get('type', 'sqlite')

        logger.info(f"Database type: {db_type}")

        # Get database connection
        db = DatabaseFactory.get_database(config)

        # Get SQL statements for this database type
        sql_statements = create_tables_sql(db_type)

        # Execute migration
        for sql in sql_statements:
            try:
                db.execute_query(sql)
                logger.info(f"✅ Executed migration statement")
            except Exception as e:
                logger.error(f"❌ Migration failed: {e}")
                logger.error(f"SQL: {sql[:100]}...")
                raise

        logger.info("✅ Migration completed successfully!")

        # Close connection
        db.close()

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


def verify_connection(environment: str = 'development'):
    """Verify database connection for specified environment

    Args:
        environment: Environment name
    """
    logger.info(f"Verifying connection for environment: {environment}")

    try:
        config = get_config(environment)
        db = DatabaseFactory.get_database(config)

        # Test query
        result = db.fetch_one("SELECT 1")
        if result:
            logger.info("✅ Database connection successful!")
        else:
            logger.warning("⚠️ Connection successful but test query returned no result")

        db.close()
        return True

    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Database migration utility')
    parser.add_argument('--env', default='development', help='Environment name')
    parser.add_argument('--verify', action='store_true', help='Verify connection only')

    args = parser.parse_args()

    if args.verify:
        verify_connection(args.env)
    else:
        migrate_database(args.env)
