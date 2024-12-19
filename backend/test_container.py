import asyncio
from app.containers import Container
from app.models.user import User
from app.models.conversation import Conversation

async def main():
    # Initialize container
    container = Container()
    container.config.from_yaml('config.yaml')
    container.wire(modules=[__name__])
    
    # Get managers from the container
    manager_factory = container.manager_factory()
    user_manager = manager_factory.user_manager
    conversation_manager = manager_factory.conversation_manager
    
    # Create a test user
    test_user = await user_manager.create_user(
        username="test_user",
        email="test@example.com"
    )
    print(f"Created user: {test_user.username}")
    
    # Create a conversation
    conversation = await conversation_manager.create_conversation(
        user_id=test_user.id,
        title="Test Conversation"
    )
    print(f"Created conversation: {conversation.title}")
    
    # Add a message to the conversation
    updated_conversation = await conversation_manager.add_message(
        conversation_id=conversation.id,
        message={
            "role": "user",
            "content": "Hello, this is a test message!"
        }
    )
    print("Added message to conversation")
    
    # Get conversation messages
    messages = await conversation_manager.get_conversation_messages(
        conversation_id=conversation.id
    )
    print("Conversation messages:", messages)
    
    # Test voice service
    voice_service = container.voice_service_provider()
    print("Voice service initialized")

if __name__ == "__main__":
    asyncio.run(main()) 