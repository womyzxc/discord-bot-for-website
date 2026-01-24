"""
Offcialx Database Module
========================
SQLite/PostgreSQL database for persistent storage.
Automatically selects the appropriate database based on environment.
"""

import os

# Factory function that selects the right database
async def get_database():
    """Get the appropriate database based on environment"""
    database_url = os.getenv('DATABASE_URL', '')

    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        from .postgres import PostgresDatabase
        db = PostgresDatabase(database_url)
        await db.connect()
        return db
    else:
        from .db import Database
        db = Database()
        await db.connect()
        return db

# For direct imports
from .db import Database, init_database

__all__ = ['Database', 'init_database', 'get_database']
