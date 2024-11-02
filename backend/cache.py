import os
import aioredis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")  # e.g., "redis://localhost"

redis = aioredis.from_url(REDIS_URL, decode_responses=True)

CACHE_TTL = 3 * 60 * 60  # 3 hours

async def get_conversation_cache(conversation_id: str):
    return await redis.get(f"conversation:{conversation_id}")

async def set_conversation_cache(conversation_id: str, data: str):
    await redis.set(f"conversation:{conversation_id}", data, ex=CACHE_TTL)