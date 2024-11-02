from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Message(BaseModel):
    id : str
    role: str
    content: str


class ConversationBase(BaseModel):
    id : str
    title: str

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: str
    messages: List[Message] = []

class ChatRequest(BaseModel):
    conversation_id: str
    message: Message

