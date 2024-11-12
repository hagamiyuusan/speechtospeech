# from app.containers import Container
# from pathlib import Path
# from dotenv import load_dotenv
# def configure_container(container: Container):

#     path = Path(__file__).resolve().parent.parent / '.env'
#     load_dotenv(path)

#     # Configure the container for document store
#     container.config.document_store.uri.from_env("DOCUMENT_STORE_URI")
#     container.config.document_store.table_name.from_env("DOCUMENT_STORE_TABLE_NAME")
#     container.config.document_store.top_k.from_env("DOCUMENT_STORE_TOP_K")
    
#     # Configure the container for vector store
#     container.config.vector_store.collection_name.from_env("VECTOR_STORE_COLLECTION_NAME")
#     container.config.vector_store.path.from_env("VECTOR_STORE_PATH")

#     # Configure the container for embedder
#     container.config.embedder.api_key.from_env("OPENAI_API_KEY")

#     # Configure the container for llm
#     container.config.llm.api_key.from_env("OPENAI_API_KEY")
#     container.config.llm.model_name.from_env("OPENAI_MODEL")

#     container.config.redis.url.from_env("REDIS_URL")
    
#     container.config.kafka.bootstrap_servers.from_env("KAFKA_BOOTSTRAP_SERVERS")
#     container.config.kafka.topic_messages.from_env("KAFKA_TOPIC_MESSAGES")
#     container.config.kafka.topic_responses.from_env("KAFKA_TOPIC_RESPONSES")
#     return container

# from openai import AsyncOpenAI
# import os
# from dotenv import load_dotenv

# load_dotenv()

# client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# async def generateTitle(messages: str):
#     messages = [{"role": "user", "content":
#                 f"Generate a title for this conversation, this is first message: {messages}"}]
#     response = await client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=messages,
#         temperature=0.5
#     )
#     return response.choices[0].message.content

