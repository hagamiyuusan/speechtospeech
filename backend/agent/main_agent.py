import sys
sys.path.append("..")
from base import IRAGHandler
from base import BaseLLM
from base import IAgent
from typing import List
from dependency_injector.wiring import inject, Provide
from uuid import  uuid4
from schemas import Message
from .utils import SYSTEM_PROMPT_MAIN_AGENT
class MainAgent(IAgent):
    @inject
    def __init__(self, llm_handler: BaseLLM = None, rag_handler: IRAGHandler = None ):
        self.llm_handler = llm_handler
        self.rag_handler = rag_handler
        self.agent_functions = {
            "rag_handler": lambda query: self.rag_handler.generate_response(table_name="asian", query=query, model_name="gpt-4o")
        }
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

    async def response(self, messages: List[dict]):
        print(messages)
        message_objects = []
        for msg in messages:
            if isinstance(msg, dict):
                if 'id' not in msg:
                    msg['id'] = str(uuid4())
                message_objects.append(Message(**msg))
            else:
                message_objects.append(msg)
        if not message_objects or message_objects[0].role != "system":
            message_objects.insert(0, Message(
                id=str(uuid4()),
                role="system",
                content=self.system_prompt
            ))
        messages_dicts = [{"role": message.role, "content": message.content} for message in message_objects]
        return self.llm_handler.stream_response(
            messages=messages_dicts,
            tools=self.tools,
            function_map=self.agent_functions,
        )




