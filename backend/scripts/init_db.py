import asyncio
import sys
from pathlib import Path
from passlib.context import CryptContext
from sqlalchemy import text

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from app.database import init_models, async_session, engine
from app.models.user import User
from app.models.workspace import Workspace
from app.models.agent import Agent
from create_db import create_database

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def drop_tables():
    tables = [
        "conversations",
        "agents",
        "workspace_users",
        "workspaces",
        "users"
    ]
    async with engine.begin() as conn:
        for table in tables:
            await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

async def create_sample_data():
    async with async_session() as session:
        async with session.begin():
            # Create admin user
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=pwd_context.hash("admin"),
                is_active=True
            )
            session.add(admin)
            await session.flush()  # This will populate the admin.id
            print(f"Created admin user with ID: {admin.id}")

            # Create default workspace
            workspace = Workspace(
                name="Default Workspace",
                collection_name="default_collection",
                admin_id=admin.id,
                users=[admin]  # This will automatically create the workspace_users relationship
            )
            session.add(workspace)
            await session.flush()
            print(f"Created workspace with ID: {workspace.id}")

            # Create default agent
            agent = Agent(
                name="Default Agent",
                system_prompt="You are a helpful AI assistant.",
                workspace_id=workspace.id
            )
            session.add(agent)
            await session.flush()
            print(f"Created agent with ID: {agent.id}")

            await session.commit()

async def init_db():
    try:
        # Create database if it doesn't exist
        await create_database()
        
        # Drop existing tables
        print("Dropping existing tables...")
        await drop_tables()
        print("Tables dropped successfully!")
        
        # Initialize models (this creates the tables)
        print("\nCreating database tables...")
        await init_models()
        print("Tables created successfully!")
        
        # Create sample data
        print("\nCreating sample data...")
        await create_sample_data()
        print("Sample data created successfully!")
            
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(init_db()) 