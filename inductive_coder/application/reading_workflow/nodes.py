"""Node functions for the Reading workflow."""

from typing import Any

from pydantic import BaseModel, Field
from langchain_core.tools import tool

from inductive_coder.domain.entities import Code, CodeBook
from inductive_coder.infrastructure.llm_client import get_llm_client, get_node_model
from inductive_coder.application.reading_workflow.prompts import (
    get_read_document_prompts,
    get_create_codebook_prompts,
)
from inductive_coder.application.reading_workflow.state import ReadingStateDict
from inductive_coder.application.tools import read_document_from_file, grep_search_directory


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
    """Create code book from accumulated notes with tool support.
    
    The LLM can use the following tools:
    - read_document_from_file: Read documents to gather additional context
    - grep_search_directory: Search for specific patterns in documents
    """
    notes = state["notes"]
    user_context = state["user_context"]
    mode = state["mode"]
    hierarchy_depth = state["hierarchy_depth"]
    documents = state["documents"]
    
    # Get directory from first document if available
    document_dir = "."
    if documents:
        document_dir = str(documents[0].path.parent)
    
    # Wrap tools with @tool decorator for LangChain compatibility
    @tool
    def read_file(file_name: str, directory: str = document_dir) -> str:
        """Read a document from a file in the specified directory."""
        return read_document_from_file(file_name, directory)
    
    @tool
    def search_directory(pattern: str, directory: str = document_dir) -> list[str]:
        """Search for a pattern in files within a directory using grep."""
        return grep_search_directory(pattern, directory)
    
    llm = get_llm_client(model=get_node_model("CREATE_CODEBOOK_MODEL"))
    
    # Get system and user prompts
    system_prompt, user_prompt = get_create_codebook_prompts(
        mode=mode.value,
        user_context=user_context,
        all_notes=notes,
        hierarchy_depth=hierarchy_depth,
    )
    
    # Add tool availability information to the prompt
    tool_info = """
You have access to the following tools to help create the codebook:
1. read_file(file_name, directory) - Read a specific document file to get more context
2. search_directory(pattern, directory) - Search for patterns in documents to understand patterns better

Use these tools to gather additional context if needed before creating the final codebook.
"""
    
    enhanced_prompt = tool_info + "\n" + user_prompt

    # Use generate_with_tools for tool calling capability
    response_text = await llm.generate_with_tools(
        prompt=enhanced_prompt,
        tools=[read_file, search_directory],
        system_prompt=system_prompt,
    )
    
    # Now generate structured response from the response text
    # We need to call generate_structured with the context from tool calls
    final_prompt = f"""Based on the following analysis, create a valid JSON codebook:

{response_text}

Return the codebook as a valid JSON object matching the CodeBookSchema."""
    
    response = await llm.generate_structured(
        prompt=final_prompt,
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
