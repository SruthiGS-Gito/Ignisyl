# Database Migration Guide - Ignisyl

## Overview

The Ignisyl application now supports **SQLite, PostgreSQL, and MySQL** databases through a robust abstraction layer. This guide walks you through setup and migration.

## What's New

### ✅ Created Files

1. **[backend/database/db_factory.py](backend/database/db_factory.py)** - Core abstraction layer
   - `DatabaseConnection` abstract base class
   - `SQLiteConnection` implementation
   - `PostgreSQLConnection` implementation (with connection pooling)
   - `MySQLConnection` implementation (with connection pooling)
   - `DatabaseFactory` for easy database switching

2. **[backend/config/database_config.py](backend/config/database_config.py)** - Environment configurations
   - `development` (SQLite)
   - `testing` (In-memory SQLite)
   - `production` (PostgreSQL)
   - `production_mysql` (MySQL)
   - `docker_postgres` (Docker PostgreSQL)
   - `docker_mysql` (Docker MySQL)

3. **[backend/database/migrate.py](backend/database/migrate.py)** - Migration utilities
   - Database table creation for all DB types
   - Connection verification
   - Command-line interface

4. **[backend/database/README.md](backend/database/README.md)** - Comprehensive documentation
   - Usage examples
   - Configuration guide
   - Troubleshooting

5. **[backend/database/example_usage.py](backend/database/example_usage.py)** - Practical examples
   - CRUD operations
   - Batch operations
   - Transaction management
   - Error handling

6. **[.env.example](.env.example)** - Environment configuration template

### ✅ Updated Files

1. **[backend/models/database.py](backend/models/database.py)** - Updated to use factory pattern
   - Automatically detects environment
   - Falls back to SQLite if factory unavailable
   - Maintains backward compatibility

2. **[requirements.txt](requirements.txt)** - Added database drivers
   - `psycopg2-binary>=2.9.9` (PostgreSQL)
   - `mysql-connector-python>=8.2.0` (MySQL)

## Quick Start

### 1. Install Dependencies

```bash
pip install psycopg2-binary mysql-connector-python
```

### 2. Choose Your Database

#### Option A: Continue with SQLite (No changes needed)

```bash
# Already configured - just run the application
export ENVIRONMENT=development
python backend/main.py
```

#### Option B: Setup PostgreSQL

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE ignisyl;
CREATE USER ignisyl_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ignisyl TO ignisyl_user;
\q

# Configure environment
export ENVIRONMENT=production
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ignisyl
export DB_USER=ignisyl_user
export DB_PASSWORD=secure_password

# Run migration
python backend/database/migrate.py --env production

# Start application
python backend/main.py
```

#### Option C: Setup MySQL

```bash
# Install MySQL
sudo apt-get install mysql-server

# Create database
sudo mysql
CREATE DATABASE ignisyl;
CREATE USER 'ignisyl_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON ignisyl.* TO 'ignisyl_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Configure environment
export ENVIRONMENT=production_mysql
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=ignisyl
export DB_USER=ignisyl_user
export DB_PASSWORD=secure_password

# Run migration
python backend/database/migrate.py --env production_mysql

# Start application
python backend/main.py
```

#### Option D: Use Docker

**PostgreSQL:**
```bash
docker run -d \
  --name ignisyl-postgres \
  -e POSTGRES_DB=ignisyl \
  -e POSTGRES_USER=ignisyl_user \
  -e POSTGRES_PASSWORD=ignisyl_password \
  -p 5432:5432 \
  postgres:15

export ENVIRONMENT=docker_postgres
python backend/database/migrate.py --env docker_postgres
python backend/main.py
```

**MySQL:**
```bash
docker run -d \
  --name ignisyl-mysql \
  -e MYSQL_DATABASE=ignisyl \
  -e MYSQL_USER=ignisyl_user \
  -e MYSQL_PASSWORD=ignisyl_password \
  -e MYSQL_ROOT_PASSWORD=root_password \
  -p 3306:3306 \
  mysql:8

export ENVIRONMENT=docker_mysql
python backend/database/migrate.py --env docker_mysql
python backend/main.py
```

## Configuration

### Using Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Example `.env` for PostgreSQL:
```
ENVIRONMENT=production
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ignisyl
DB_USER=ignisyl_user
DB_PASSWORD=secure_password
```

### Using Configuration File

Edit `backend/config/database_config.py`:

```python
DATABASE_CONFIG = {
    'my_custom_env': {
        'type': 'postgresql',
        'host': 'db.example.com',
        'port': 5432,
        'database': 'ignisyl',
        'user': 'ignisyl_user',
        'password': 'secure_password'
    }
}
```

## Migration Process

### Verify Connection

```bash
python backend/database/migrate.py --env production --verify
```

### Run Migration

```bash
python backend/database/migrate.py --env production
```

### Example Output

```
INFO:__main__:Starting migration for environment: production
INFO:__main__:Database type: postgresql
✅ Using POSTGRESQL database for environment: production
INFO:__main__:✅ Executed migration statement
INFO:__main__:✅ Executed migration statement
INFO:__main__:✅ Executed migration statement
INFO:__main__:✅ Migration completed successfully!
```

## Testing the Abstraction Layer

Run the example script:

```bash
python backend/database/example_usage.py
```

This will demonstrate:
- Basic CRUD operations
- Batch inserts
- Transaction management
- Different database types
- Error handling

## Architecture

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│    (FastAPI, ML Engine, etc.)          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Database Factory Pattern           │
│                                         │
│  DatabaseFactory.get_database(config)  │
└─────────┬───────┬──────────┬───────────┘
          │       │          │
    ┌─────▼──┐ ┌──▼─────┐ ┌─▼────────┐
    │ SQLite │ │ Postgres│ │  MySQL   │
    │ Connection│ │ Connection│ │ Connection│
    └────────┘ └─────────┘ └──────────┘
```

## API Usage

### Direct Usage

```python
from backend.database.db_factory import DatabaseFactory
from backend.config.database_config import get_config

# Get connection
config = get_config('production')
db = DatabaseFactory.get_database(config)

# Execute queries
db.execute_query(
    "INSERT INTO users (username, email) VALUES (?, ?)",
    ('john.doe', 'john@example.com')
)

# Fetch data
users = db.fetch_all("SELECT * FROM users")

# Close connection
db.close()
```

### Transaction Management

```python
with db.transaction():
    db.execute_query("UPDATE users SET role = ? WHERE id = ?", ('Admin', 1))
    db.execute_query("INSERT INTO system_logs (message) VALUES (?)", ('User promoted',))
    # Automatically commits on success, rolls back on error
```

## Performance Comparison

| Feature | SQLite | PostgreSQL | MySQL |
|---------|--------|------------|-------|
| Concurrency | Single writer | Multiple writers | Multiple writers |
| Connection Pool | No | Yes (1-10) | Yes (10) |
| Network Support | No | Yes | Yes |
| ACID Compliance | Yes | Yes | Yes |
| Best For | Development | Production | Web Apps |

## Security Considerations

1. **Never hardcode credentials** - Use environment variables
2. **Use parameterized queries** - Already implemented in abstraction layer
3. **Limit database user privileges** - Grant only required permissions
4. **Enable SSL/TLS** - For production databases
5. **Regular backups** - Automate database backups

## Troubleshooting

### "Module not found: psycopg2"

```bash
pip install psycopg2-binary
```

### "Module not found: mysql.connector"

```bash
pip install mysql-connector-python
```

### Connection Refused

- Check database is running: `sudo systemctl status postgresql` or `sudo systemctl status mysql`
- Verify firewall rules
- Check credentials in `.env`

### Permission Denied

PostgreSQL:
```sql
GRANT ALL PRIVILEGES ON DATABASE ignisyl TO ignisyl_user;
```

MySQL:
```sql
GRANT ALL PRIVILEGES ON ignisyl.* TO 'ignisyl_user'@'localhost';
FLUSH PRIVILEGES;
```

### SQLAlchemy Compatibility

The application uses SQLAlchemy ORM, which now automatically detects the database type through the updated `backend/models/database.py`.

## Rollback to SQLite

If you encounter issues, simply switch back:

```bash
export ENVIRONMENT=development
python backend/main.py
```

## Next Steps

1. ✅ Install database dependencies
2. ✅ Choose your database (SQLite/PostgreSQL/MySQL)
3. ✅ Configure environment variables
4. ✅ Run migration script
5. ✅ Test with example script
6. ✅ Start application

## Support

For detailed documentation, see:
- [backend/database/README.md](backend/database/README.md) - Full API reference
- [backend/database/example_usage.py](backend/database/example_usage.py) - Practical examples
- [backend/config/database_config.py](backend/config/database_config.py) - Configuration options

## Summary

The database abstraction layer provides:
- ✅ **Multi-database support** (SQLite, PostgreSQL, MySQL)
- ✅ **Production-ready** with connection pooling
- ✅ **Thread-safe** operations
- ✅ **Transaction management** with context managers
- ✅ **Error handling** and logging
- ✅ **Easy migration** between databases
- ✅ **Backward compatible** with existing code

No changes to existing application code are required - the system automatically detects and uses the configured database!
