"""
OpenAI LLM integration with streaming and function calling.
"""
import os
import json
from typing import List, Dict, Any, AsyncGenerator, Optional
from datetime import datetime
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMHandler:
    """Handles LLM streaming and function calling."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        
        # Define available tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get the current date and time in ISO format",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool call.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result as string
        """
        if tool_name == "get_current_time":
            return self._get_current_time()
        else:
            return f"Unknown tool: {tool_name}"
    
    def _get_current_time(self) -> str:
        """Get current time in ISO format."""
        return datetime.utcnow().isoformat() + "Z"
    
    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        session_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream LLM completion with function calling support.
        
        Args:
            messages: Conversation history
            session_id: Current session ID
            
        Yields:
            Dictionaries with streaming events:
            - {"type": "token", "content": "..."}
            - {"type": "tool_call", "tool_name": "...", "tool_id": "..."}
            - {"type": "tool_result", "content": "..."}
            - {"type": "done"}
        """
        try:
            # First API call with tools
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                stream=True,
                temperature=0.7
            )
            
            tool_calls = []
            current_tool_call = None
            assistant_message = ""
            
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                
                if not delta:
                    continue
                
                # Handle tool calls
                if delta.tool_calls:
                    for tool_call_chunk in delta.tool_calls:
                        if tool_call_chunk.index is not None:
                            # New tool call
                            while len(tool_calls) <= tool_call_chunk.index:
                                tool_calls.append({
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                })
                            
                            current_tool_call = tool_calls[tool_call_chunk.index]
                            
                            if tool_call_chunk.id:
                                current_tool_call["id"] = tool_call_chunk.id
                            
                            if tool_call_chunk.function:
                                if tool_call_chunk.function.name:
                                    current_tool_call["function"]["name"] = tool_call_chunk.function.name
                                if tool_call_chunk.function.arguments:
                                    current_tool_call["function"]["arguments"] += tool_call_chunk.function.arguments
                
                # Handle regular content
                if delta.content:
                    assistant_message += delta.content
                    yield {
                        "type": "token",
                        "content": delta.content
                    }
            
            # If tool calls were made, execute them and continue
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_id = tool_call["id"]
                    
                    # Parse arguments
                    try:
                        arguments = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    # Notify client about tool call
                    yield {
                        "type": "tool_call",
                        "tool_name": tool_name,
                        "tool_id": tool_id
                    }
                    
                    # Execute tool
                    tool_result = self.execute_tool(tool_name, arguments)
                    
                    # Add tool call and result to messages
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": tool_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(arguments)
                            }
                        }]
                    })
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": tool_result
                    })
                    
                    # Yield tool result
                    yield {
                        "type": "tool_result",
                        "tool_name": tool_name,
                        "content": tool_result
                    }
                
                # Second API call with tool results
                stream2 = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    temperature=0.7
                )
                
                async for chunk in stream2:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    
                    if delta and delta.content:
                        yield {
                            "type": "token",
                            "content": delta.content
                        }
            
            yield {"type": "done"}
            
        except Exception as e:
            yield {
                "type": "error",
                "content": f"LLM error: {str(e)}"
            }
    
    async def generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a concise summary of the conversation.
        
        Args:
            messages: Full conversation history
            
        Returns:
            Summary text
        """
        try:
            summary_prompt = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates concise summaries of conversations. Summarize the key points and outcomes in 2-3 sentences."
                },
                {
                    "role": "user",
                    "content": f"Please summarize this conversation:\n\n{json.dumps(messages, indent=2)}"
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=summary_prompt,
                temperature=0.5,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Failed to generate summary: {str(e)}"



# Lazy LLM handler initialization
_llm_handler_instance = None

def get_llm_handler() -> LLMHandler:
    """Get or create LLM handler instance."""
    global _llm_handler_instance
    if _llm_handler_instance is None:
        _llm_handler_instance = LLMHandler()
    return _llm_handler_instance

# For backward compatibility
llm_handler = None
