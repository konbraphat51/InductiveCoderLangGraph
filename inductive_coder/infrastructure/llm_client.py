"""LLM client implementation using OpenAI."""

import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
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
        # Use structured output with Pydantic schema
        structured_llm = self.llm.with_structured_output(schema)
        
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        messages.append(HumanMessage(content=prompt))
        
        response = await structured_llm.ainvoke(messages)
        
        # Convert Pydantic model to dict
        if isinstance(response, BaseModel):
            return response.model_dump()
        return response


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
