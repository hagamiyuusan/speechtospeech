import asyncio
from pathlib import Path
import sys
from uuid import uuid4

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from app.containers import Container
from app.config import load_config

async def main():
    # Initialize and configure the container
    container = Container()
    config = load_config()
    container.config.from_dict(config)
    
    # Get the manager factory from container
    manager_factory = container.manager_factory()
    
    try:
        # Create a test user with direct DB access (MVP without security)
        user_data = {
            "id": str(uuid4()),
            "username": "test_user",
            "email": "test@example.com",
            "is_active": True
        }
        db = container.db_session()
        test_user = await db.execute(
            "INSERT INTO users (id, username, email, is_active) VALUES (:id, :username, :email, :is_active) RETURNING *",
            user_data
        )
        test_user = test_user.fetchone()
        await db.commit()
        
        # Create a workspace
        workspace_manager = manager_factory.workspace_manager
        workspace = await workspace_manager.create_workspace(
            name="Test Workspace",
            admin_id=test_user.id,
            collection_name="test_collection"
        )
        
        # Create an agent for the workspace
        agent_manager = manager_factory.agent_manager
        agent = await agent_manager.create_agent(
            workspace_id=workspace.id,
            agent_config={
                "name": "Test Agent",
                "system_prompt": "You are a helpful AI assistant.",
                "tools_config": {}
            }
        )
        
        # Create a conversation
        conversation_manager = manager_factory.conversation_manager
        conversation = await conversation_manager.create_conversation(
            user_id=test_user.id,
            title="Test Conversation"
        )
        
        # Send a message and get response
        chat_service = container.chat_service()
        
        # Example conversation
        messages = [
            {
                "role": "user",
                "content": "Hello! Can you help me understand how this chat system works?"
            }
        ]
        
        response = await chat_service.process_message(
            conversation_id=conversation.id,
            workspace_id=workspace.id,
            messages=messages
        )
        
        print("\nChat Example Output:")
        print(f"User ID: {test_user.id}")
        print(f"Workspace ID: {workspace.id}")
        print(f"Conversation ID: {conversation.id}")
        print("\nUser: Hello! Can you help me understand how this chat system works?")
        print(f"Assistant: {response}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 