import sys
sys.path.append("..")
from base import BaseLLM
from openai import AsyncOpenAI
import json

class LLMHandler(BaseLLM):
    def __init__(self, api_key: str, model_name = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = model_name

    async def generate_response(self, messages: list[dict] | str, tools: list = None, function_map : dict = None, model_name: str = None):
        user_messages = messages.copy()
        if tools and function_map:
            response = await self.client.chat.completions.create(
                model= model_name if model_name else self.model_name,
                messages=user_messages,
                temperature=0.1,
                tools=tools,
                tool_choice= "auto")
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            if not tool_calls:
                return response_message.content
            else:
                user_messages.append(response_message)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    if function_name in function_map:
                        function_response = await function_map[function_name](**function_args)
                        user_messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        })
                return await self.generate_response(user_messages, tools, function_map)

        else:
            response = await self.client.chat.completions.create(
                model=model_name if model_name else self.model_name,
                messages=user_messages,
                temperature=0.3,
                stream=False  # Make sure this is False for reranking
            )
            return response.choices[0].message.content
    

    async def stream_response(self, messages: list[dict] | str, tools: list = None, function_map: dict = None, model_name: str = None):
        user_messages = messages.copy()
        if tools and function_map:
            response = await self.client.chat.completions.create(
                model=model_name if model_name else self.model_name,
                messages=user_messages,
                temperature=0.1,
                tools=tools,
                tool_choice="auto",
                stream=True  # Enable streaming
            )

            streaming_content = ""
            tool_calls = []
            
            async for chunk in response:
                if not chunk.choices:
                    yield "Sorry, there was an error. Please try again."
                    break
                
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    streaming_content += delta.content
                    yield delta.content
                elif delta and delta.tool_calls:
                    tcchunklist = delta.tool_calls
                    for tcchunk in tcchunklist:
                        if len(tool_calls) <= tcchunk.index:
                            tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                        tc = tool_calls[tcchunk.index]
                        if tcchunk.id:
                            tc["id"] = tcchunk.id
                        if tcchunk.function.name:
                            tc["function"]["name"] += tcchunk.function.name
                        if tcchunk.function.arguments:
                            tc["function"]["arguments"] += tcchunk.function.arguments
                
                elif chunk.choices[0].finish_reason == "tool_calls" and tool_calls:
                    user_messages.append({
                        "tool_calls": tool_calls,
                        "role": 'assistant',
                    })
                    
                    for tool_call in tool_calls:
                        function_name = tool_call['function']['name']
                        if function_name in function_map:
                            function_args = json.loads(tool_call['function']['arguments'])
                            function_response = await function_map[function_name](**function_args)
                            user_messages.append({
                                "tool_call_id": tool_call['id'],
                                "role": "tool",
                                "name": function_name,
                                "content": str(function_response),
                            })
                    
                    tool_calls = []
                    async for content in self.stream_response(user_messages, tools, function_map):
                        yield content
            if streaming_content:
                user_messages.append({"role": "assistant", "content": streaming_content})

        else:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content



