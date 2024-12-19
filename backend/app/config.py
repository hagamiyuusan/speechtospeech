import os
from pathlib import Path
from dotenv import load_dotenv

def load_config():
    """Load configuration from environment variables"""
    # Load .env file if it exists
    env_path = Path(__file__).resolve().parent.parent / '.env'
    load_dotenv(env_path)
    
    return {
        "database": {
            "url": os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/docstore")
        },
        "document_store": {
            "uri": os.getenv("DOCUMENT_STORE_URI", "postgresql://localhost:5432/docstore"),
            "top_k": int(os.getenv("DOCUMENT_STORE_TOP_K", "5"))
        },
        "vector_store": {
            "path": os.getenv("VECTOR_STORE_PATH", "./vector_store")
        },
        "embedder": {
            "api_key": os.getenv("OPENAI_API_KEY")
        },
        "llm": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model_name": os.getenv("OPENAI_MODEL", "gpt-4"),
            "groq_api_key": os.getenv("GROQ_API_KEY")
        },
        "redis": {
            "url": os.getenv("REDIS_URL", "redis://localhost:6379")
        }
    } 