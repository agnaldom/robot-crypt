#!/usr/bin/env python3
"""
Comprehensive database schema migration script
Drops old tables and recreates them with correct schema
"""
import os
import sys
import logging
import psycopg2
from psycopg2.extras import DictCursor

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def migrate_database():
    """Perform database migration"""
    logger = setup_logging()
    
    try:
        # Connect to database directly
        connection_string = os.environ.get("POSTGRES_URL")
        if not connection_string:
            logger.error("POSTGRES_URL environment variable not found")
            return False
            
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        logger.info("Connected to PostgreSQL database for migration")
        
        # Tables that need to be recreated with correct schema
        tables_to_recreate = [
            'asset_balances',
            'app_state', 
            'trades',
            'transaction_history',
            'user_wallet'  # Already dropped but just in case
        ]
        
        # Drop all problematic tables
        for table_name in tables_to_recreate:
            logger.info(f"Dropping table: {table_name}")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
            conn.commit()
            logger.info(f"  ✓ Dropped table {table_name}")
        
        # Drop indices that might exist
        indices_to_drop = [
            'idx_asset_balances_user_asset',
            'idx_asset_balances_snapshot_date',
            'idx_asset_balances_updated_at',
            'idx_asset_balances_usdt_value',
            'idx_user_wallet_user_asset',
            'idx_user_wallet_timestamp'
        ]
        
        for index_name in indices_to_drop:
            try:
                cursor.execute(f"DROP INDEX IF EXISTS {index_name};")
                conn.commit()
                logger.info(f"  ✓ Dropped index {index_name}")
            except Exception as e:
                logger.warning(f"  - Could not drop index {index_name}: {e}")
        
        # Close connection before using PostgresManager
        cursor.close()
        conn.close()
        
        # Now use PostgresManager to create tables with correct schema
        logger.info("Creating tables with correct schema using PostgresManager...")
        
        # Import and initialize PostgresManager
        from src.database.postgres_manager import PostgresManager
        pm = PostgresManager()
        
        logger.info("Database migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during database migration: {str(e)}")
        return False

def main():
    """Main function"""
    logger = setup_logging()
    
    print("=== Database Migration Tool ===")
    print("This will drop existing tables and recreate them with the correct schema.")
    print("WARNING: This will delete all existing data in the affected tables.")
    print("")
    
    response = input("Are you sure you want to proceed? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        logger.info("Starting database migration...")
        if migrate_database():
            logger.info("Database migration completed successfully!")
            return 0
        else:
            logger.error("Database migration failed!")
            return 1
    else:
        logger.info("Migration cancelled by user")
        return 0

if __name__ == "__main__":
    exit(main())
