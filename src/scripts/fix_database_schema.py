#!/usr/bin/env python3
"""
Script to diagnose and fix database schema issues
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

from src.database.postgres_manager import PostgresManager

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]

def get_table_columns(cursor, table_name):
    """Get columns of a table"""
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    return cursor.fetchall()

def diagnose_database_schema():
    """Diagnose current database schema"""
    logger = setup_logging()
    
    try:
        # Connect to database directly
        connection_string = os.environ.get("POSTGRES_URL")
        if not connection_string:
            logger.error("POSTGRES_URL environment variable not found")
            return False
            
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        logger.info("Connected to PostgreSQL database")
        
        # Check problematic tables
        tables_to_check = [
            'user_wallet',
            'asset_balances',
            'app_state',
            'trades',
            'transaction_history'
        ]
        
        for table_name in tables_to_check:
            logger.info(f"\nChecking table: {table_name}")
            
            if check_table_exists(cursor, table_name):
                logger.info(f"  ✓ Table {table_name} exists")
                columns = get_table_columns(cursor, table_name)
                logger.info(f"  Columns ({len(columns)}):")
                for col in columns:
                    logger.info(f"    - {col['column_name']} ({col['data_type']}, nullable: {col['is_nullable']})")
                    
                # Check for user_id column specifically
                has_user_id = any(col['column_name'] == 'user_id' for col in columns)
                if has_user_id:
                    logger.info(f"  ✓ Table {table_name} has user_id column")
                else:
                    logger.warning(f"  ⚠ Table {table_name} does NOT have user_id column")
            else:
                logger.info(f"  - Table {table_name} does not exist")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error diagnosing database schema: {str(e)}")
        return False

def fix_database_schema():
    """Fix database schema issues"""
    logger = setup_logging()
    
    try:
        # Connect to database directly
        connection_string = os.environ.get("POSTGRES_URL")
        if not connection_string:
            logger.error("POSTGRES_URL environment variable not found")
            return False
            
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor(cursor_factory=DictCursor)
        
        logger.info("Connected to PostgreSQL database for schema fixes")
        
        # Drop problematic old tables that might have wrong schema
        old_tables = ['user_wallet']
        
        for table_name in old_tables:
            if check_table_exists(cursor, table_name):
                logger.info(f"Dropping old table: {table_name}")
                cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                conn.commit()
                logger.info(f"  ✓ Dropped table {table_name}")
            else:
                logger.info(f"  - Table {table_name} does not exist (ok)")
        
        # Close connection before using PostgresManager
        cursor.close()
        conn.close()
        
        # Now use PostgresManager to create tables with correct schema
        logger.info("Creating tables with correct schema using PostgresManager...")
        pm = PostgresManager()
        
        logger.info("Database schema fixed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing database schema: {str(e)}")
        return False

def main():
    """Main function"""
    logger = setup_logging()
    
    print("=== Database Schema Diagnosis and Fix Tool ===\n")
    
    # First diagnose
    logger.info("Step 1: Diagnosing current database schema...")
    if not diagnose_database_schema():
        logger.error("Failed to diagnose database schema")
        return 1
    
    # Ask user if they want to fix
    print("\n" + "="*50)
    response = input("Do you want to fix the database schema? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        logger.info("Step 2: Fixing database schema...")
        if fix_database_schema():
            logger.info("Database schema fixed successfully!")
            
            # Diagnose again to verify
            logger.info("Step 3: Verifying fixes...")
            if diagnose_database_schema():
                logger.info("Verification successful!")
                return 0
            else:
                logger.error("Verification failed")
                return 1
        else:
            logger.error("Failed to fix database schema")
            return 1
    else:
        logger.info("Skipping schema fixes")
        return 0

if __name__ == "__main__":
    exit(main())
