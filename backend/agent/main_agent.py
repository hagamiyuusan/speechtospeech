import sys
sys.path.append("..")
from base import IRAGHandler
from base import BaseLLM
from typing import Dict, Any, List
from dependency_injector.wiring import inject, Provide
from uuid import UUID, uuid4
from schemas import Message
from .utils import SYSTEM_PROMPT_MAIN_AGENT
class MainAgent:
    @inject
    def __init__(self, llm_handler: BaseLLM = None, rag_handler: IRAGHandler = None):
        self.llm_handler = llm_handler
        self.rag_handler = rag_handler
        self.agent_functions = {
            "rag_handler": self.rag_handler.generate_response,

        }
        self.conversation_history = []
        self.system_prompt = SYSTEM_PROMPT_MAIN_AGENT.format(tools=str(list(self.agent_functions.keys())))
        self.tools = [
            {
                'type': 'function',
                'function': {
                    'name': 'rag_handler',
                    'description': """
                        When users ask questions related to ASEAN, you must definitely use this tool
                    """,
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': """
                                    The user's question about ASEAN.
                                """
                            }
                        },
                        'required': ['query']
                    }
                }
            }

        ]

    # async def generate_response(self, id: UUID, user_input: str) -> str:
    #     conversation_history = await self.chat_service.load_conversation(id)
    #     conversation_history.append({"id": UUID(), "role": "user", "content": user_input})

    #     response = await self.llm_handler.stream_response(messages = conversation_history, 
    #                                                         tools=self.tools,
    #                                                         function_map=self.agent_functions)
    #     temp_conversation = conversation_history.copy()
    #     temp_conversation.append({"role": "assistant", "content": response})
    #     await self.chat_service.update_chat_history(id, temp_conversation)
    #     return response
    async def response(self, messages: List[dict]):
        print(messages)
        # Convert dict messages to Message objects if needed
        message_objects = []
        for msg in messages:
            if isinstance(msg, dict):
                message_objects.append(Message(**msg))
            else:
                message_objects.append(msg)
                
        # Add system prompt if not present
        if not message_objects or message_objects[0].role != "system":
            message_objects.insert(0, Message(
                id=str(uuid4()),
                role="system",
                content=self.system_prompt
            ))
            
        # Convert to format expected by LLM handler
        messages_dicts = [
            {"role": message.role, "content": message.content} 
            for message in message_objects
        ]

        # Return the generator directly instead of awaiting it
        return self.llm_handler.stream_response(
            messages=messages_dicts,
            tools=self.tools,
            function_map=self.agent_functions
        )



