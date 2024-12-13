from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from app.containers import Container
from app.services import ChatService
from app.schema import ChatRequest, ConversationBase, ChatAudioRequest
from typing import List, Generator, Dict, AsyncGenerator  # Added AsyncGenerator here
from uuid import UUID
import asyncio
import uvicorn
from dependency_injector.wiring import inject
import json
from fastapi import UploadFile, File, Form
app = FastAPI()
import base64
import io
from app.schema import Message
from uuid import uuid4
from asyncio import Queue
import re

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences while preserving punctuation."""
    # Basic sentence splitting on .!?
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def chunk_text(text: str, min_chunk_size: int = 50) -> Generator[str, None, None]:
    """Yield chunks of text, trying to break at sentence boundaries."""
    buffer = ""
    sentences = split_into_sentences(text)
    
    for sentence in sentences:
        buffer += sentence + " "
        if len(buffer) >= min_chunk_size:
            yield buffer.strip()
            buffer = ""
    
    if buffer:  # Don't forget the last piece
        yield buffer.strip()

# Configure container
container = Container()
container.config.from_yaml('config.yaml')
container.wire(modules=[__name__])
class StreamBuffer:
    def __init__(self, min_chunk_size: int = 50):
        self.current_buffer = ""
        self.min_chunk_size = min_chunk_size

    def add_text(self, text: str) -> Generator[str, None, None]:
        """Add text to buffer and return complete chunks."""
        self.current_buffer += text
        
        # Only split on actual sentence endings
        if any(end in self.current_buffer for end in ['.', '!', '?']):
            sentences = split_into_sentences(self.current_buffer)
            
            # Keep the last potentially incomplete sentence in the buffer
            if self.current_buffer[-1] not in ['.', '!', '?']:
                self.current_buffer = sentences[-1]
                sentences = sentences[:-1]
            else:
                self.current_buffer = ""
            
            buffer = ""
            for sentence in sentences:
                if len(sentence) > self.min_chunk_size:
                    # Yield long sentences directly
                    yield sentence.strip()
                    continue
                
                buffer += sentence + " "
                if len(buffer) >= self.min_chunk_size:
                    yield buffer.strip()
                    buffer = ""
            
            # Update current buffer with remaining content
            if buffer:
                self.current_buffer = buffer.strip() + " " + self.current_buffer


class TTSManager:
    def __init__(self):
        self.voice_settings: Dict[str, dict] = {
            "default": {"model": "tts-1", "voice": "alloy"},
            "casual": {"model": "tts-1", "voice": "nova"},
            "formal": {"model": "tts-1", "voice": "onyx"}
        }
        self.client = container.openai_client()

    async def process_chunk(self, text: str, voice_style: str = "default") -> AsyncGenerator[bytes, None]:
        settings = self.voice_settings.get(voice_style, self.voice_settings["default"])
        client = self.client
        
        try:
            async with client.audio.speech.with_streaming_response.create(
                    model=settings["model"],
                    voice=settings["voice"],
                    input=text,
                    response_format="wav",
                    speed=1.0
            ) as response:
                async for chunk in response.iter_bytes(4096):
                    yield chunk
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            raise



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
tts_manager = TTSManager()




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
            try:
                data = await websocket.receive_json()
                if manager.is_processing(websocket):
                    manager.set_processing(websocket, False)
                    await websocket.send_json({
                        "type": "interrupt",
                        "message": "Previous request interrupted"
                    })
                    await asyncio.sleep(0.5)

                if 'conversation_id' not in data or 'audio_data' not in data:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Missing required fields"
                    })
                    continue

                manager.set_processing(websocket, True)
                
                conversation_id = data['conversation_id']
                audio_data = data['audio_data']
                
                audio_bytes = base64.b64decode(audio_data)
                audio_file = UploadFile(
                    file=io.BytesIO(audio_bytes),
                    filename="audio.wav"
                )

                conversation_id_uuid = UUID(conversation_id)
                transcript = await stt_service.generate_audio(audio_file)

                print(transcript)
                if transcript["no_speech_prob"] < 0.1:
                    await websocket.send_json({
                        "type": "transcript",
                        "text": transcript["text"],
                        "language": transcript["language"]
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No speech detected"
                    })
                    continue
                
                question = f"{transcript['text']}. You must answer in {transcript['language']}. Helpful answer:"
                message = Message(id=str(uuid4()), role="user", content=question)
                
                stream_buffer = StreamBuffer()
                processing_queue = asyncio.Queue()

                async def process_tts(sentence: str):
                    try:
                        print(sentence)
                        await websocket.send_json({
                            "type": "text_response",
                            "text": sentence
                        })
                        async for audio_chunk in tts_manager.process_chunk(sentence):
                            if not manager.is_processing(websocket):
                                break
                            await websocket.send_json({
                                "type": "audio_chunk",
                                "audio": base64.b64encode(audio_chunk).decode('utf-8')
                            })
                        await websocket.send_json({
                            "type": "sentence_complete",
                            "sentence": sentence
                        })
                    except Exception as e:
                        logger.error(f"TTS processing error: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"TTS error: {str(e)}",
                            "sentence": sentence
                        })
                async def process_queue():
                    while manager.is_processing(websocket):
                        try:
                            sentence = await processing_queue.get()
                            await process_tts(sentence)
                            processing_queue.task_done()
                        except asyncio.CancelledError:
                            break
                        except Exception as e:
                            logger.error(f"Queue processing error: {str(e)}")
    
                queue_processor = asyncio.create_task(process_queue())

                # Get complete text response
                text_response = ""
                async for chunk in chat_service.chat_response(conversation_id_uuid, message):
                    if not manager.is_processing(websocket):
                        break
                    json_chunk = json.loads(chunk)

                    if "content" in json_chunk:
                        text_response += json_chunk["content"]
                        complete_sentences = list(stream_buffer.add_text(json_chunk["content"]))
                        print(complete_sentences)
                        for sentence in complete_sentences:
                            await processing_queue.put(sentence)
                        await websocket.send_json({
                            "type": "text_delta",
                            "text": json_chunk["content"]
                        })
                    if "full_response" in json_chunk:
                        text_response = json_chunk["full_response"]

                        if stream_buffer.current_buffer:
                            await processing_queue.put(stream_buffer.current_buffer.strip())
                            stream_buffer.current_buffer = ""
 

                await processing_queue.join()
                queue_processor.cancel()


                if manager.is_processing(websocket):    
                    await websocket.send_json({
                        "type": "audio_complete"
                    })
                
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

    async with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="alloy",
            input=text,
            response_format ="wav"
    ) as response:
        async for chunk in response.iter_bytes(4096):
            yield chunk



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
    language = transcript["language"]
    transcription = transcript["text"]

    question = f"{transcription}. Please answer in {language}. Helpful answer:"
    # Create a proper Message object

    message = Message(id=str(uuid4()), role="user", content=question)
    
    text_response = ""
    # Pass the Message object instead of the transcript string
    async for chunk in chat_service.chat_response(conversation_id, message):
        json_chunk = json.loads(chunk)
        if "full_response" in json_chunk:
            text_response += json_chunk["full_response"]
    
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