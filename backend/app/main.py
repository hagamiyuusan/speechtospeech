# app/main_async.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile
from pydantic import BaseModel
from typing import List
from dependency_injector.wiring import inject, Provide
from containers import Container
from database import AsyncSessionLocal, init_db
from sqlalchemy.ext.asyncio import AsyncSession
from agent.main_agent import MainAgent
import uvicorn
from pathlib import Path
from dotenv import load_dotenv
from .utils import configure_container
from typing import AsyncGenerator
import os

root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

app = FastAPI()
container = Container()

container = configure_container(container)

container.wire(modules=[__name__])

@app.on_event("startup")
async def on_startup():
    await init_db()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

class ChatRequest(BaseModel):
    user_id: str
    user_input: str


class ChatResponse(BaseModel):
    response: str

class IndexFileRequest(BaseModel):
    file: UploadFile



@app.get("/")
async def root():
    print("Hello World")
    return {"message": "Hello World"}

@app.post("/chat/", response_model=ChatResponse)
@inject
async def chat(
    request: ChatRequest,
    main_agent: MainAgent = Depends(Provide[Container.main_agent])
):
    print(request)
    try:
        response = await main_agent.generate_response(str(request.user_id), request.user_input)
        return ChatResponse(response=response)
    
    except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
