"""Node functions for the Reading workflow."""

from typing import Any

from pydantic import BaseModel, Field

from inductive_coder.domain.entities import Code, CodeBook
from inductive_coder.infrastructure.llm_client import get_llm_client, get_node_model
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
    parent_code_name: str | None = Field(default=None, description="Name of parent code if this is a sub-code (hierarchical structure)")


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
    
    llm = get_llm_client(model=get_node_model("READ_DOCUMENT_MODEL"))
    
    # Get system and user prompts (with current notes context)
    system_prompt, user_prompt = get_read_document_prompts(
        mode=mode.value,
        user_context=user_context,
        doc_name=doc.path.name,
        doc_content=doc.content,
        current_notes=current_notes
    )

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
    hierarchy_depth = state["hierarchy_depth"]
    
    llm = get_llm_client(model=get_node_model("CREATE_CODEBOOK_MODEL"))
    
    # Get system and user prompts
    system_prompt, user_prompt = get_create_codebook_prompts(
        mode=mode.value,
        user_context=user_context,
        all_notes=notes,
        hierarchy_depth=hierarchy_depth,
    )

    response = await llm.generate_structured(
        prompt=user_prompt,
        schema=CodeBookSchema,
        system_prompt=system_prompt,
    )
    
    # Convert to domain entities
    codes = [
        Code(
            name=c["name"], 
            description=c["description"], 
            criteria=c["criteria"],
            parent_code_name=c.get("parent_code_name")
        )
        for c in response["codes"]
    ]
    
    code_book = CodeBook(codes=codes, mode=mode, context=user_context, hierarchy_depth=hierarchy_depth)
    
    return {"code_book": code_book}
