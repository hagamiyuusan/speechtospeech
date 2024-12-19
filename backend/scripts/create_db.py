import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# Load environment variables from .env file if it exists
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

async def create_database(drop_if_exists=False):
    # Connection parameters for the default postgres database
    conn_params = {
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "huy778631"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": "postgres"  # Connect to default postgres database first
    }

    try:
        print("Attempting to connect to PostgreSQL...")
        # Connect to default postgres database
        conn = await asyncpg.connect(**conn_params)
        print("Connected successfully to PostgreSQL")
        
        # Check if our database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            "new_system"
        )
        
        if exists and drop_if_exists:
            print("Dropping existing database 'new_system'...")
            # Terminate all connections to the database before dropping
            await conn.execute("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'new_system'
                AND pid <> pg_backend_pid();
            """)
            await conn.execute("DROP DATABASE new_system")
            exists = False
            print("Database 'new_system' dropped successfully")
        
        if not exists:
            print("Creating database 'new_system'...")
            # Create database if it doesn't exist
            await conn.execute("CREATE DATABASE new_system")
            print("Database 'new_system' created successfully")
        else:
            print("Database 'new_system' already exists")
            
        await conn.close()
        print("Database connection closed")
        
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        raise

if __name__ == "__main__":
    drop_if_exists = "--drop" in sys.argv
    asyncio.run(create_database(drop_if_exists)) 