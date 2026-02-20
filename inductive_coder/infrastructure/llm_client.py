"""LLM client implementation using OpenAI."""

import json
import os
from typing import Any, Callable

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from pydantic import BaseModel

from inductive_coder.domain.repositories import ILLMClient

# Load environment variables
load_dotenv()


class OpenAILLMClient(ILLMClient):
    """OpenAI LLM client implementation."""
    
    def __init__(
        self,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.3,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
        )
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: str | None = None
    ) -> str:
        """Generate a response from the LLM."""
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        messages.append(HumanMessage(content=prompt))
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def generate_structured(
        self, 
        prompt: str, 
        schema: type[BaseModel],
        system_prompt: str | None = None
    ) -> dict[str, Any]:
        """Generate a structured response matching the given schema."""
        # Use function_calling method for compatibility with optional/default fields
        structured_llm = self.llm.with_structured_output(schema, method="function_calling")
        
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        messages.append(HumanMessage(content=prompt))
        
        response = await structured_llm.ainvoke(messages)
        
        # Convert Pydantic model to dict
        if isinstance(response, BaseModel):
            return response.model_dump()
        return response
    
    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[Callable],
        system_prompt: str | None = None,
        max_iterations: int = 10
    ) -> str:
        """Generate a response with tool calling capabilities.
        
        Args:
            prompt: The user prompt
            tools: List of tool functions that LLM can call
            system_prompt: Optional system prompt
            max_iterations: Maximum number of tool calling iterations
            
        Returns:
            The final response from the LLM
        """
        # Bind tools to the LLM
        llm_with_tools = self.llm.bind_tools(tools)
        
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        messages.append(HumanMessage(content=prompt))
        
        # Tool calling loop
        for _ in range(max_iterations):
            response = await llm_with_tools.ainvoke(messages)
            
            # If no tool calls, return the response
            if not response.tool_calls:
                return response.content
            
            # Add the response to messages
            messages.append(response)
            
            # Process tool calls
            for tool_call in response.tool_calls:
                tool_result = await self._execute_tool_call(tool_call, tools)
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=tool_result
                ))
        
        # Return final response after max iterations
        return response.content
    
    async def _execute_tool_call(self, tool_call: dict, tools: list[Callable]) -> str:
        """Execute a tool call and return the result."""
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})
        
        # Find the matching tool
        for t in tools:
            if hasattr(t, "name"):
                if t.name == tool_name:
                    try:
                        result = t(**tool_args)
                        # Handle async tools
                        if hasattr(result, '__await__'):
                            result = await result
                        return str(result)
                    except Exception as e:
                        return f"Error calling tool {tool_name}: {str(e)}"
        
        return f"Tool {tool_name} not found"


# Global LLM client instances keyed by model name
_llm_clients: dict[str, OpenAILLMClient] = {}


def get_node_model(node_model_env_key: str) -> str:
    """Resolve model name for a node-specific environment key.

    Falls back to OPENAI_MODEL and then a built-in default model.
    """
    return (
        os.getenv(node_model_env_key)
        or os.getenv(node_model_env_key.lower())
        or os.getenv("OPENAI_MODEL")
        or "gpt-4-turbo-preview"
    )


def get_llm_client(model: str | None = None) -> OpenAILLMClient:
    """Get or create an LLM client instance for the given model."""
    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    if resolved_model not in _llm_clients:
        _llm_clients[resolved_model] = OpenAILLMClient(model=resolved_model)

    return _llm_clients[resolved_model]


def set_llm_client(client: OpenAILLMClient, model: str | None = None) -> None:
    """Set an LLM client instance for a model key."""
    model_key = model or client.model
    _llm_clients[model_key] = client
