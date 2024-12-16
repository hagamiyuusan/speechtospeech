import json
from typing import List, AsyncGenerator
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

from schemas import Message

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generateTitle(messages: str):
    messages = [{"role": "user", "content":
                f"Generate a title for this conversation, this is first message: {messages}"}]
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.5
    )
    return response.choices[0].message.content

async def generate_response_chunks(message: List[Message]):
    print(message)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=message,
        temperature=0.5,
        stream=True
    )
    full_response = ""
    async for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_response += content
            yield json.dumps({"content": content}) + "\n"
    
    # Return the full response at the end
    yield json.dumps({"full_response": full_response}) + "\n"

async def generateResponse(messages: List[Message]) -> StreamingResponse:
    return StreamingResponse(
        generate_response_chunks(messages),
        media_type="text/event-stream"
    )


