"""Node functions for the Reading workflow."""

from typing import Any

from pydantic import BaseModel, Field

from inductive_coder.domain.entities import Code, CodeBook
from inductive_coder.infrastructure.llm_client import get_llm_client
from inductive_coder.application.reading_workflow.prompts import (
    get_read_document_prompts,
    get_create_codebook_prompts,
)
from inductive_coder.application.reading_workflow.state import ReadingStateDict


# Pydantic schemas for structured output

class CodeSchema(BaseModel):
    """Schema for a single code."""
    name: str = Field(description="Short, descriptive name for the code")
    description: str = Field(description="What this code represents")
    criteria: str = Field(description="When to apply this code")


class CodeBookSchema(BaseModel):
    """Schema for the code book."""
    codes: list[CodeSchema] = Field(description="List of codes to use for analysis")


# Node functions

async def read_document_node(state: ReadingStateDict) -> dict[str, Any]:
    """Read a document and take notes."""
    current_idx = state["current_doc_index"]
    documents = state["documents"]
    
    if current_idx >= len(documents):
        return {"current_doc_index": current_idx}
    
    doc = documents[current_idx]
    user_context = state["user_context"]
    mode = state["mode"]
    current_notes = state["notes"]
    
    llm = get_llm_client()
    
    # Get system and user prompts
    system_prompt, user_prompt = get_read_document_prompts(
        mode=mode.value,
        user_context=user_context,
        doc_name=doc.path.name,
        doc_content=doc.content
    )
    
    # Add current notes context if exists
    if current_notes:
        system_prompt += f"\n\nYour current notes (long-term memory):\n{current_notes}\n\nYou can update or expand these notes based on the new document."

    response = await llm.generate(user_prompt, system_prompt=system_prompt)
    
    return {
        "notes": response,  # Replace notes with new version
        "current_doc_index": current_idx + 1,
    }


async def create_codebook_node(state: ReadingStateDict) -> dict[str, Any]:
    """Create code book from accumulated notes."""
    notes = state["notes"]
    user_context = state["user_context"]
    mode = state["mode"]
    
    llm = get_llm_client()
    
    # Get system and user prompts
    system_prompt, user_prompt = get_create_codebook_prompts(
        mode=mode.value,
        user_context=user_context,
        all_notes=notes
    )

    response = await llm.generate_structured(
        prompt=user_prompt,
        schema=CodeBookSchema,
        system_prompt=system_prompt,
    )
    
    # Convert to domain entities
    codes = [
        Code(name=c["name"], description=c["description"], criteria=c["criteria"])
        for c in response["codes"]
    ]
    
    code_book = CodeBook(codes=codes, mode=mode, context=user_context)
    
    return {"code_book": code_book}
