"""Database configuration for different environments"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent

DATABASE_CONFIG = {
    'development': {
        'type': 'sqlite',
        'path': str(BASE_DIR / 'data' / 'ignisyl.db')
    },

    'testing': {
        'type': 'sqlite',
        'path': ':memory:'  # In-memory database for tests
    },

    'production': {
        'type': os.getenv('DB_TYPE', 'postgresql'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'ignisyl'),
        'user': os.getenv('DB_USER', 'ignisyl_user'),
        'password': os.getenv('DB_PASSWORD', 'secure_password')
    },

    'production_mysql': {
        'type': 'mysql',
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'database': os.getenv('DB_NAME', 'ignisyl'),
        'user': os.getenv('DB_USER', 'ignisyl_user'),
        'password': os.getenv('DB_PASSWORD', 'secure_password')
    },

    'docker_postgres': {
        'type': 'postgresql',
        'host': os.getenv('DB_HOST', 'postgres'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'ignisyl'),
        'user': os.getenv('DB_USER', 'ignisyl_user'),
        'password': os.getenv('DB_PASSWORD', 'ignisyl_password')
    },

    'docker_mysql': {
        'type': 'mysql',
        'host': os.getenv('DB_HOST', 'mysql'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'database': os.getenv('DB_NAME', 'ignisyl'),
        'user': os.getenv('DB_USER', 'ignisyl_user'),
        'password': os.getenv('DB_PASSWORD', 'ignisyl_password')
    }
}


def get_config(environment: str = None):
    """Get database configuration for specified environment

    Args:
        environment: Environment name. If None, uses ENVIRONMENT env var or 'development'

    Returns:
        Database configuration dictionary
    """
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'development')

    if environment not in DATABASE_CONFIG:
        raise ValueError(f"Unknown environment: {environment}. Available: {list(DATABASE_CONFIG.keys())}")

    return DATABASE_CONFIG[environment]
