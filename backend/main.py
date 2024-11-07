import json
import uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Conversation, Base
from schemas import ChatRequest, ConversationBase,  Message
from cache import get_conversation_cache, set_conversation_cache
import uvicorn
from typing import List
from uuid import UUID
from utils import generateTitle, generate_response_chunks
from fastapi.middleware.cors import CORSMiddleware
from app.containers import Container


app = FastAPI()

container = Container()
container.config.from_yaml('config.yaml')
container.wire(modules=[__name__])



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Create database tables

async def get_conversation(id: UUID, db: AsyncSession = Depends(co)):
    result = await db.execute(select(Conversation).where(Conversation.id == id))
    convo = result.scalars().first()
    return convo



async def create_conversation(conversation_id: UUID, title: str, messages: List[dict], db: AsyncSession):
    # Ensure messages are list of dicts
    messages_dicts = []
    for message in messages:
        if isinstance(message, Message):
            messages_dicts.append(message.dict())
        elif isinstance(message, dict):
            messages_dicts.append(message)
        else:
            raise ValueError('Messages must be list of dicts or Message objects')
    new_convo = Conversation(id=conversation_id, title=title, messages=messages_dicts)
    db.add(new_convo)
    await db.commit()
    await db.refresh(new_convo)
    return new_convo  # Return the Conversation object

# @app.post("/conversations/{conversation_id}/messages/", response_model=Message)
# async def add_message(conversation_id: UUID, message: Message, db: AsyncSession = Depends(get_db)):
#     # Check if conversation exists
#     result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
#     convo = result.scalars().first()
#     if not convo:
#         raise HTTPException(status_code=404, detail="Conversation not found")
    
#     if message.role not in ['user', 'assistant']:
#         raise HTTPException(status_code=400, detail="Invalid role")

#     # Append the new message with timestamp
#     new_message = {
#         "role": message.role,
#         "content": message.content,
#     }

#     convo.messages.append(new_message)
#     db.add(convo)
#     await db.commit()
#     await db.refresh(convo)
    
#     message_response = Message(
#         role=new_message["role"],
#         content=new_message["content"],
#     )
    
#     # Invalidate cache for this conversation
#     await set_conversation_cache(str(conversation_id), "null")
    
#     return message_response


@app.post("/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    conversation_id = UUID(request.conversation_id)
    message = request.message

    # Convert the incoming message to a dictionary
    message_dict = message.dict()

    # Fetch the conversation from the database
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    convo = result.scalars().first()

    if not convo:
        print("Creating new conversation")
        title = await generateTitle(message.content)
        convo = Conversation(
            id=conversation_id,
            title=title,
            messages=[message_dict]
        )
        db.add(convo)
        await db.commit()
        await db.refresh(convo)
    else:
        convo.messages.append(message_dict)
        db.add(convo)
        await db.commit()
        await db.refresh(convo)

    async def process_messages():
        # Convert messages from dicts to Message models
        messages = [Message(**msg) for msg in convo.messages]
        response_generator = generate_response_chunks(messages)

        async for chunk in response_generator:
            chunk_data = json.loads(chunk)
            if "full_response" in chunk_data:
                assistant_message = {
                    "id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": chunk_data["full_response"]
                }
                # Append the assistant's response to the conversation
                convo.messages.append(assistant_message)
                db.add(convo)
                await db.commit()
                await db.refresh(convo)

                # Invalidate the cache for this conversation
                await set_conversation_cache(str(conversation_id), "null")
            yield chunk

    return StreamingResponse(process_messages(), media_type="text/event-stream")

# get conversation by id
@app.get("/conversation/{conversation_id}")
async def load_conversation(conversation_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    convo = result.scalars().first()
    return convo

# get all conversations
@app.get("/conversations/", response_model=List[ConversationBase])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conversation))
    convos = result.scalars().all()
    return [ConversationBase(
        id=str(convo.id),
        title=convo.title,
    ) for convo in convos]



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


