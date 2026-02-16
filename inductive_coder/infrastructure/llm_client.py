"""LLM client implementation using OpenAI."""

import json
import os
from typing import Optional, Any

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
        system_prompt: Optional[str] = None
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
        system_prompt: Optional[str] = None
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


# Global LLM client instance
_llm_client: Optional[OpenAILLMClient] = None


def get_llm_client() -> OpenAILLMClient:
    """Get or create the global LLM client instance."""
    global _llm_client
    
    if _llm_client is None:
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        _llm_client = OpenAILLMClient(model=model)
    
    return _llm_client


def set_llm_client(client: OpenAILLMClient) -> None:
    """Set the global LLM client instance."""
    global _llm_client
    _llm_client = client
