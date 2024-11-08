from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from app.containers import Container
from app.services import ChatService
from schemas import ChatRequest, ConversationBase
from typing import List
from uuid import UUID
import uvicorn
from dependency_injector.wiring import inject
import json
import io

app = FastAPI()

# Configure container
container = Container()
container.config.from_yaml('config.yaml')
container.wire(modules=[__name__])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://b431-171-243-224-241.ngrok-free.app",
                   "https://*.ngrok-free.app",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_chat_service():
    return container.chat_service()

@app.post("/chat")
@inject
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    conversation_id = UUID(request.conversation_id)
    message = request.message
    
    async def stream_response():
        try:
            async for chunk in chat_service.stream_response(conversation_id, message):
                yield chunk
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"
        finally:
            # Ensure stream completion
            yield json.dumps({"done": True}) + "\n"
            
    return StreamingResponse(stream_response(), media_type="text/event-stream")

@app.get("/conversation/{conversation_id}")
@inject
async def load_conversation(
    conversation_id: UUID,
    chat_service: ChatService = Depends(get_chat_service)
):
    return await chat_service.load_conversation(conversation_id)

@app.get("/conversations/", response_model=List[ConversationBase])
@inject
async def list_conversations(
    chat_service: ChatService = Depends(get_chat_service)
):
    return await chat_service.list_conversations()


@app.post("/tts")
async def text_to_speech(request: dict):
    print(request)
    client = container.openai_client()
    response = await client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=request["text"]    )
    
    async def stream_audio():
        CHUNK_SIZE = 1024 * 8  # 8KB chunks
        audio_content = response.content
        for i in range(0, len(audio_content), CHUNK_SIZE):
            yield audio_content[i:i + CHUNK_SIZE]
    
    return StreamingResponse(
        stream_audio(),
        media_type="audio/mpeg",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Type": "audio/mpeg",
            "Access-Control-Allow-Origin": "https://b431-171-243-224-241.ngrok-free.app",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)