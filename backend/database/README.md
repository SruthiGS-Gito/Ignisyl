# Database Abstraction Layer - Ignisyl

Production-ready database abstraction layer supporting SQLite, PostgreSQL, and MySQL.

## Features

- **Multiple Database Support**: SQLite, PostgreSQL, MySQL
- **Connection Pooling**: Automatic connection pooling for PostgreSQL and MySQL
- **Thread-Safe**: Safe for concurrent operations
- **Transaction Support**: Context manager for transactions
- **Error Handling**: Comprehensive error logging and recovery
- **Factory Pattern**: Easy database switching via configuration

## Architecture

```
backend/database/
├── __init__.py           # Package exports
├── db_factory.py         # Factory and connection implementations
├── migrate.py            # Migration utilities
└── README.md            # This file

backend/config/
├── __init__.py
└── database_config.py    # Environment configurations
```

## Quick Start

### 1. Install Dependencies

```bash
pip install psycopg2-binary mysql-connector-python
```

### 2. Configure Environment

Set the `ENVIRONMENT` variable to choose your database:

```bash
# Development (SQLite)
export ENVIRONMENT=development

# Production (PostgreSQL)
export ENVIRONMENT=production
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ignisyl
export DB_USER=ignisyl_user
export DB_PASSWORD=secure_password

# Production (MySQL)
export ENVIRONMENT=production_mysql
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=ignisyl
export DB_USER=ignisyl_user
export DB_PASSWORD=secure_password
```

### 3. Run Migration

```bash
# Verify connection
python backend/database/migrate.py --env production --verify

# Run migration
python backend/database/migrate.py --env production
```

## Configuration

Edit `backend/config/database_config.py` for custom configurations:

```python
DATABASE_CONFIG = {
    'development': {
        'type': 'sqlite',
        'path': 'data/ignisyl.db'
    },
    'production': {
        'type': 'postgresql',
        'host': 'localhost',
        'port': 5432,
        'database': 'ignisyl',
        'user': 'ignisyl_user',
        'password': 'secure_password'
    }
}
```

## Usage Examples

### Using the Factory Pattern

```python
from backend.database.db_factory import DatabaseFactory
from backend.config.database_config import get_config

# Get database connection
config = get_config('production')
db = DatabaseFactory.get_database(config)

# Execute query
db.execute_query(
    "INSERT INTO users (username, email) VALUES (?, ?)",
    ('john.doe', 'john@example.com')
)

# Fetch data
users = db.fetch_all("SELECT * FROM users WHERE department = ?", ('IT',))

# Use transactions
with db.transaction():
    db.execute_query("UPDATE users SET role = ? WHERE id = ?", ('Admin', 1))
    db.execute_query("INSERT INTO system_logs (message) VALUES (?)", ('User promoted',))
    # Automatically commits on success, rolls back on error

# Close connection
db.close()
```

### Direct Connection Usage

```python
from backend.database.db_factory import SQLiteConnection, PostgreSQLConnection

# SQLite
sqlite_db = SQLiteConnection({'path': 'data/ignisyl.db'})
sqlite_db.connect()

# PostgreSQL
postgres_db = PostgreSQLConnection({
    'host': 'localhost',
    'port': 5432,
    'database': 'ignisyl',
    'user': 'ignisyl_user',
    'password': 'secure_password'
})
postgres_db.connect()
```

### Batch Operations

```python
# Insert multiple rows efficiently
users_data = [
    ('alice', 'alice@example.com'),
    ('bob', 'bob@example.com'),
    ('charlie', 'charlie@example.com')
]

db.execute_many(
    "INSERT INTO users (username, email) VALUES (?, ?)",
    users_data
)
```

## Database Setup

### PostgreSQL Setup

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE ignisyl;
CREATE USER ignisyl_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ignisyl TO ignisyl_user;
\q

# Run migration
python backend/database/migrate.py --env production
```

### MySQL Setup

```bash
# Install MySQL
sudo apt-get install mysql-server

# Create database and user
sudo mysql
CREATE DATABASE ignisyl;
CREATE USER 'ignisyl_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON ignisyl.* TO 'ignisyl_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Run migration
python backend/database/migrate.py --env production_mysql
```

### Docker Setup

#### PostgreSQL with Docker

```bash
docker run -d \
  --name ignisyl-postgres \
  -e POSTGRES_DB=ignisyl \
  -e POSTGRES_USER=ignisyl_user \
  -e POSTGRES_PASSWORD=ignisyl_password \
  -p 5432:5432 \
  postgres:15

# Set environment
export ENVIRONMENT=docker_postgres
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ignisyl
export DB_USER=ignisyl_user
export DB_PASSWORD=ignisyl_password
```

#### MySQL with Docker

```bash
docker run -d \
  --name ignisyl-mysql \
  -e MYSQL_DATABASE=ignisyl \
  -e MYSQL_USER=ignisyl_user \
  -e MYSQL_PASSWORD=ignisyl_password \
  -e MYSQL_ROOT_PASSWORD=root_password \
  -p 3306:3306 \
  mysql:8

# Set environment
export ENVIRONMENT=docker_mysql
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=ignisyl
export DB_USER=ignisyl_user
export DB_PASSWORD=ignisyl_password
```

## Migration from SQLite to PostgreSQL/MySQL

### Step 1: Backup SQLite Data

```bash
sqlite3 data/ignisyl.db .dump > backup.sql
```

### Step 2: Setup New Database

Follow PostgreSQL or MySQL setup instructions above.

### Step 3: Run Migration

```bash
python backend/database/migrate.py --env production
```

### Step 4: Export and Import Data

For PostgreSQL:
```bash
# Convert SQLite dump to PostgreSQL format (manual editing may be needed)
# Import data
psql -h localhost -U ignisyl_user -d ignisyl < converted_backup.sql
```

For MySQL:
```bash
# Convert SQLite dump to MySQL format (manual editing may be needed)
# Import data
mysql -h localhost -u ignisyl_user -p ignisyl < converted_backup.sql
```

## Connection Pooling

Connection pooling is automatically configured for PostgreSQL and MySQL:

- **PostgreSQL**: 1-10 connections (SimpleConnectionPool)
- **MySQL**: 10 connections (MySQLConnectionPool)
- **SQLite**: Single connection with thread safety

## Error Handling

All database operations include comprehensive error handling:

```python
try:
    db.execute_query("INSERT INTO users (username) VALUES (?)", ('test',))
except Exception as e:
    logger.error(f"Database error: {e}")
    # Error is logged with full context
    # Transaction is automatically rolled back
```

## Performance Considerations

### SQLite
- Best for: Development, small deployments, embedded systems
- Limitations: Single writer, no network access
- Performance: Excellent for read-heavy workloads

### PostgreSQL
- Best for: Production, complex queries, high concurrency
- Features: Advanced indexing, full ACID compliance, JSON support
- Performance: Excellent for both read and write operations

### MySQL
- Best for: Web applications, high-traffic sites
- Features: Fast reads, replication, clustering
- Performance: Optimized for web workloads

## Security Best Practices

1. **Never hardcode credentials** - Use environment variables
2. **Use parameterized queries** - Prevent SQL injection
3. **Limit privileges** - Database user should have minimal required permissions
4. **Enable SSL/TLS** - For production database connections
5. **Regular backups** - Automate database backups

## Troubleshooting

### Connection Issues

```python
# Test connection
python backend/database/migrate.py --env production --verify
```

### Import Errors

```bash
# Install missing dependencies
pip install psycopg2-binary mysql-connector-python
```

### Permission Errors

```sql
-- PostgreSQL
GRANT ALL PRIVILEGES ON DATABASE ignisyl TO ignisyl_user;

-- MySQL
GRANT ALL PRIVILEGES ON ignisyl.* TO 'ignisyl_user'@'localhost';
FLUSH PRIVILEGES;
```

## API Reference

### DatabaseConnection (Abstract Base Class)

- `connect()` - Establish database connection
- `execute_query(query, params)` - Execute INSERT/UPDATE/DELETE
- `execute_many(query, params_list)` - Batch execute
- `fetch_one(query, params)` - Fetch single row
- `fetch_all(query, params)` - Fetch all rows
- `commit()` - Commit transaction
- `rollback()` - Rollback transaction
- `close()` - Close connection
- `transaction()` - Context manager for transactions

### DatabaseFactory

- `get_database(config)` - Create database connection from config
- `get_database_from_env(environment)` - Create from environment name

## Testing

```python
# Unit tests
pytest backend/tests/test_database.py

# Integration tests
pytest backend/tests/test_database_integration.py
```

## License

This database abstraction layer is part of the Ignisyl project.

## Support

For issues or questions:
1. Check this README
2. Review database logs
3. Test connection with `--verify` flag
4. Check database permissions
