import asyncio
import asyncpg

async def check_db():
    # Connect to the database
    conn = await asyncpg.connect(
        user='postgres',
        password='huy778631',
        database='new_system',
        host='localhost'
    )

    try:
        # Get list of tables
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_catalog.pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        
        print("\nTables in database:")
        for table in tables:
            print(f"- {table['tablename']}")
            
        # Check each table's contents
        for table in tables:
            table_name = table['tablename']
            print(f"\nContents of {table_name}:")
            rows = await conn.fetch(f'SELECT * FROM {table_name}')
            if not rows:
                print("(empty)")
            else:
                for row in rows:
                    print(row)
                
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_db()) 