from pydantic import BaseModel, Field
from typing import List, Annotated
from datetime import datetime
from fastapi import UploadFile

class Message(BaseModel):
    id : str
    role: str
    content: str

class MessageAudio(BaseModel):
    id : str
    role: str
    content: UploadFile

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

class ChatAudioRequest(BaseModel):
    conversation_id: str
    message: MessageAudio

