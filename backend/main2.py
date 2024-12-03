from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from app.containers import Container
from app.services import ChatService
from app.schema import ChatRequest, ConversationBase, ChatAudioRequest
from typing import List
from uuid import UUID
import uvicorn
from dependency_injector.wiring import inject
import json
from fastapi import UploadFile, File, Form
app = FastAPI()
import base64
import io
from app.schema import Message
from uuid import uuid4
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.processing_flags: dict = {}  # Track processing state for each connection

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.processing_flags[websocket] = False

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.processing_flags:
            del self.processing_flags[websocket]

    def is_processing(self, websocket: WebSocket) -> bool:
        return self.processing_flags.get(websocket, False)

    def set_processing(self, websocket: WebSocket, status: bool):
        self.processing_flags[websocket] = status

manager = ConnectionManager()


# Configure container
container = Container()
container.config.from_yaml('config.yaml')
container.wire(modules=[__name__])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_chat_service():
    return container.chat_service()

def get_stt_service():
    return container.stt()

def get_openai_client():
    return container.openai_client()


@app.websocket("/ws/audio-chat")
@inject
async def websocket_audio_chat(
    websocket: WebSocket,
    stt_service = Depends(get_stt_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    await manager.connect(websocket)
    try:
        while True:
            # Use receive_json with a timeout to allow checking for new messages
            try:
                data = await websocket.receive_json()
                
                # If we're currently processing a request, interrupt it
                if manager.is_processing(websocket):
                    manager.set_processing(websocket, False)
                    await websocket.send_json({
                        "type": "interrupt",
                        "message": "Previous request interrupted"
                    })

                # Validate incoming message
                if 'conversation_id' not in data or 'audio_data' not in data:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Missing required fields: conversation_id and audio_data"
                    })
                    continue

                # Set processing flag
                manager.set_processing(websocket, True)
                
                conversation_id = data['conversation_id']
                audio_data = data['audio_data']
                
                # Convert base64 to audio file-like object
                audio_bytes = base64.b64decode(audio_data)
                audio_file = UploadFile(
                    file=io.BytesIO(audio_bytes),
                    filename="audio.wav"
                )

                # Process audio
                conversation_id_uuid = UUID(conversation_id)
                transcript = await stt_service.generate_audio(audio_file)
                
                # Send transcript back to client
                await websocket.send_json({
                    "type": "transcript",
                    "text": transcript
                })

                message = Message(id=str(uuid4()), role="user", content=transcript)
                
                # Stream the chat response
                text_response = ""
                async for chunk in chat_service.chat_response(conversation_id_uuid, message):
                    # Check if we've been interrupted
                    if not manager.is_processing(websocket):
                        break
                        
                    json_chunk = json.loads(chunk)
                    if "full_response" in json_chunk:
                        text_response += json_chunk["full_response"]
                        # Send intermediate updates
                        await websocket.send_json({
                            "type": "text_chunk",
                            "text": json_chunk["full_response"]
                        })

                # Only proceed with audio generation if we haven't been interrupted
                if manager.is_processing(websocket) and text_response:
                    audio_content = await create_audio_from_text_without_streaming(text_response)
                    audio_base64 = base64.b64encode(audio_content).decode('utf-8')
                    
                    await websocket.send_json({
                        "type": "complete",
                        "audio": audio_base64,
                        "text": text_response
                    })
                
                # Reset processing flag
                manager.set_processing(websocket, False)

            except WebSocketDisconnect:
                raise
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                manager.set_processing(websocket, False)

    except WebSocketDisconnect:
        manager.disconnect(websocket)

@inject
@app.post("/stt")
async def  get_transcript(input: UploadFile, stt_service = Depends(get_stt_service)):
    return await stt_service.generate_audio(input)


@inject
async def create_audio_stream(text: str):
    client = container.openai_client()
    # p = pyaudio.PyAudio()
    # stream = p.open(format=8,
    #                 channels=1,
    #                 rate=24_000,
    #                 output=True)
    async with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="alloy",
            input=text,
            response_format ="wav"
    ) as response:
        async for chunk in response.iter_bytes(1024):
            # stream.write(chunk)
            yield chunk
    # stream.stop_stream()
    # stream.close()
    # p.terminate()


@inject 
async def create_audio_from_text_without_streaming(text: str):
    client = container.openai_client()
    response = await client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            response_format="wav"
    )
    return response.content

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
            async for chunk in chat_service.chat_response(conversation_id, message):
                yield chunk
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"
        finally:
            # Ensure stream completion
            yield json.dumps({"done": True}) + "\n"
            
    return StreamingResponse(stream_response(), media_type="text/event-stream")

@app.post("/audio-to-audio")
@inject
async def audio_to_audio(audio_file: UploadFile = File(...), conversation_id: str = Form(...), stt_service = Depends(get_stt_service), chat_service: ChatService = Depends(get_chat_service)):
    conversation_id = UUID(conversation_id)
    # Get transcript from STT service
    transcript = await stt_service.generate_audio(audio_file)
    
    # Create a proper Message object

    message = Message(id=str(uuid4()), role="user", content=transcript)
    
    text_response = ""
    # Pass the Message object instead of the transcript string
    async for chunk in chat_service.chat_response(conversation_id, message):
        json_chunk = json.loads(chunk)
        if "full_response" in json_chunk:
            text_response += json_chunk["full_response"]
            print(text_response)    
    
    if not text_response:
        raise HTTPException(status_code=500, detail="No response generated")
    

    async def stream_response():
        async for chunk in create_audio_stream(text_response):
            yield chunk
    return StreamingResponse(
        stream_response(),
        media_type="audio/wav",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Type": "audio/wav"
        }
    )


@app.post("/audio-to-audio-full")
@inject
async def audio_to_audio_full(
    audio_file: UploadFile = File(...), 
    conversation_id: str = Form(...), 
    stt_service = Depends(get_stt_service), 
    chat_service: ChatService = Depends(get_chat_service)
):
    conversation_id = UUID(conversation_id)
    # Get transcript from STT service
    transcript = await stt_service.generate_audio(audio_file)
    

    message = Message(id=str(uuid4()), role="user", content=transcript)
    
    text_response = ""
    # Get complete text response
    async for chunk in chat_service.chat_response(conversation_id, message):
        json_chunk = json.loads(chunk)
        if "full_response" in json_chunk:
            text_response += json_chunk["full_response"]
    
    if not text_response:
        raise HTTPException(status_code=500, detail="No response generated")

    # Use create_audio_from_text instead of collecting chunks
    audio_content = await create_audio_from_text_without_streaming(text_response)
    
    return Response(
        content=audio_content,
        media_type="audio/wav",
        headers={
            "Content-Disposition": "attachment; filename=response.wav"
        }
    )

# @app.post("/audio-to-audio-complete")
# @inject
# async def audio_to_audio_complete(
#     audio_file: UploadFile = File(...), 
#     conversation_id: str = Form(...), 
#     stt_service = Depends(get_stt_service), 
#     chat_service: ChatService = Depends(get_chat_service)
# ):
#     conversation_id = UUID(conversation_id)
#     # Get transcript from STT service
#     transcript = await stt_service.generate_audio(audio_file)
    
#     # Create a proper Message object
#     from app.schema import Message
#     from uuid import uuid4
#     message = Message(id=str(uuid4()), role="user", content=transcript)
    
#     text_response = ""
#     # Get complete text response
#     async for chunk in chat_service.chat_response(conversation_id, message):
#         json_chunk = json.loads(chunk)
#         if "full_response" in json_chunk:
#             text_response += json_chunk["full_response"]
    
#     if not text_response:
#         raise HTTPException(status_code=500, detail="No response generated")

#     # Collect all audio chunks into a single bytes object
#     audio_chunks = []
#     async for chunk in create_audio_stream(text_response):
#         audio_chunks.append(chunk)
    
#     complete_audio = b''.join(audio_chunks)
    
#     return Response(
#         content=complete_audio,
#         media_type="audio/wav",
#         headers={
#             "Content-Disposition": "attachment; filename=response.wav"
#         }
#     )





@app.post("/chat-to-audio")
@inject
async def chat_to_audio(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    conversation_id = UUID(request.conversation_id)
    message = request.message
    
    # Get the complete text response first
    text_response = ""
    async for chunk in chat_service.chat_response(conversation_id, message):
        json_chunk = json.loads(chunk)
        if "full_response" in json_chunk:
            text_response += json_chunk["full_response"]

    if not text_response:
        raise HTTPException(status_code=500, detail="No response generated")
    
    # Create the audio stream
    response = await create_audio_from_text_without_streaming(text_response)
    
    return Response(
        content=response,
        media_type="audio/wav",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Type": "audio/wav"
        }
    )

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
    async def stream_response():
        async for chunk in create_audio_stream(request["text"]):
            yield chunk
    
    return StreamingResponse(
        stream_response(),
        media_type="audio/mpeg",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Type": "audio/mpeg"
        }
    )
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)