"""Node functions for the Reading workflow."""

from typing import Any

from pydantic import BaseModel, Field
from langchain_core.tools import tool

from inductive_coder.domain.entities import Code, CodeBook
from inductive_coder.infrastructure.llm_client import get_llm_client, get_node_model
from inductive_coder.application.reading_workflow.prompts import (
    get_read_document_prompts,
    get_create_codebook_prompts,
    get_re_read_document_prompts,
    get_update_codebook_prompts,
)
from inductive_coder.application.reading_workflow.state import ReadingStateDict
from inductive_coder.application.tools import read_document_from_file, grep_search_directory
from inductive_coder.logger import logger


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
    """Read a batch of documents and take notes."""
    current_idx = state["current_doc_index"]
    documents = state["documents"]
    progress_callback = state.get("progress_callback")
    notes_file_path = state.get("notes_file_path")
    batch_size = state.get("batch_size", 1)
    
    if current_idx >= len(documents):
        return {"current_doc_index": current_idx}
    
    user_context = state["user_context"]
    mode = state["mode"]
    current_notes = state["notes"]
    total = len(documents)
    
    # Determine the batch of documents to read
    batch_end = min(current_idx + batch_size, total)
    batch_docs = documents[current_idx:batch_end]
    
    if batch_size > 1:
        logger.info(
            "[Reading] (%d-%d/%d) Start: %s",
            current_idx + 1, batch_end, total,
            ", ".join(d.path.name for d in batch_docs),
        )
    else:
        logger.info("[Reading] (%d/%d) Start: %s", current_idx + 1, total, batch_docs[0].path.name)
    
    llm = get_llm_client(model=get_node_model("READ_DOCUMENT_MODEL"))
    
    # Get system and user prompts (with current notes context)
    system_prompt, user_prompt = get_read_document_prompts(
        mode=mode.value,
        user_context=user_context,
        docs=[(d.path.name, d.content) for d in batch_docs],
        current_notes=current_notes,
    )

    response = await llm.generate(user_prompt, system_prompt=system_prompt)
    
    # Update progress
    new_idx = batch_end
    if batch_size > 1:
        logger.info("[Reading] (%d-%d/%d) Done", current_idx + 1, new_idx, total)
    else:
        logger.info("[Reading] (%d/%d) Done:  %s", new_idx, total, batch_docs[0].path.name)
    if progress_callback:
        progress_callback("Reading", new_idx, total)
    
    # Write notes to file in real-time if path provided
    if notes_file_path:
        try:
            notes_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(notes_file_path, "a", encoding="utf-8") as f:
                if batch_size > 1:
                    names = ", ".join(d.path.name for d in batch_docs)
                    f.write(f"\n## Documents {current_idx + 1}-{new_idx}/{total}: {names}\n\n")
                else:
                    f.write(f"\n## Document {new_idx}/{total}: {batch_docs[0].path.name}\n\n")
                f.write(response)
                f.write("\n")
                f.flush()
            logger.debug("[Reading] Notes written to: %s", notes_file_path)
        except Exception as e:
            logger.error("[Reading] Failed to write notes: %s", e)
    
    return {
        "notes": response,  # Replace notes with new version
        "current_doc_index": new_idx,
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
    
    logger.info("[Reading] Creating code book from %d documents...", len(documents))
    
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
    
    logger.info("[Reading] Code book created: %d codes", len(codes))
    for c in codes:
        parent_info = f" (parent: {c.parent_code_name})" if c.parent_code_name else ""
        logger.debug("[Reading]   Code: %s%s", c.name, parent_info)
    
    return {"code_book": code_book}


def _codebook_to_str(code_book: CodeBook) -> str:
    """Convert a CodeBook to a human-readable string for use in prompts."""
    lines = []
    for code in code_book.codes:
        parent_info = f" (parent: {code.parent_code_name})" if code.parent_code_name else ""
        lines.append(f"- {code.name}{parent_info}: {code.description} | Criteria: {code.criteria}")
    return "\n".join(lines)


async def re_read_document_node(state: ReadingStateDict) -> dict[str, Any]:
    """Re-read a batch of documents and note codes missing from the current codebook."""
    current_idx = state["current_doc_index"]
    documents = state["documents"]
    progress_callback = state.get("progress_callback")
    notes_file_path = state.get("notes_file_path")
    batch_size = state.get("batch_size", 1)
    current_round = state.get("current_round", 1)

    if current_idx >= len(documents):
        return {"current_doc_index": current_idx}

    user_context = state["user_context"]
    mode = state["mode"]
    current_notes = state["notes"]
    total = len(documents)
    code_book = state["code_book"]

    # Determine the batch of documents to read
    batch_end = min(current_idx + batch_size, total)
    batch_docs = documents[current_idx:batch_end]

    if batch_size > 1:
        logger.info(
            "[Re-reading round %d] (%d-%d/%d) Start: %s",
            current_round, current_idx + 1, batch_end, total,
            ", ".join(d.path.name for d in batch_docs),
        )
    else:
        logger.info(
            "[Re-reading round %d] (%d/%d) Start: %s",
            current_round, current_idx + 1, total, batch_docs[0].path.name,
        )

    llm = get_llm_client(model=get_node_model("READ_DOCUMENT_MODEL"))

    code_book_str = _codebook_to_str(code_book) if code_book else ""

    system_prompt, user_prompt = get_re_read_document_prompts(
        mode=mode.value,
        user_context=user_context,
        docs=[(d.path.name, d.content) for d in batch_docs],
        code_book_str=code_book_str,
        current_notes=current_notes if current_notes else None,
    )

    response = await llm.generate(user_prompt, system_prompt=system_prompt)

    new_idx = batch_end
    if batch_size > 1:
        logger.info("[Re-reading round %d] (%d-%d/%d) Done", current_round, current_idx + 1, new_idx, total)
    else:
        logger.info("[Re-reading round %d] (%d/%d) Done: %s", current_round, new_idx, total, batch_docs[0].path.name)
    if progress_callback:
        progress_callback(f"Re-reading (round {current_round})", new_idx, total)

    # Write notes to file in real-time if path provided
    if notes_file_path:
        try:
            notes_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(notes_file_path, "a", encoding="utf-8") as f:
                if batch_size > 1:
                    names = ", ".join(d.path.name for d in batch_docs)
                    f.write(f"\n## [Round {current_round}] Documents {current_idx + 1}-{new_idx}/{total}: {names}\n\n")
                else:
                    f.write(f"\n## [Round {current_round}] Document {new_idx}/{total}: {batch_docs[0].path.name}\n\n")
                f.write(response)
                f.write("\n")
                f.flush()
            logger.debug("[Re-reading] Notes written to: %s", notes_file_path)
        except Exception as e:
            logger.error("[Re-reading] Failed to write notes: %s", e)

    return {
        "notes": response,
        "current_doc_index": new_idx,
    }


async def update_codebook_node(state: ReadingStateDict) -> dict[str, Any]:
    """Expand the existing codebook with missing codes identified during re-reading."""
    notes = state["notes"]
    user_context = state["user_context"]
    mode = state["mode"]
    hierarchy_depth = state["hierarchy_depth"]
    documents = state["documents"]
    code_book = state["code_book"]
    current_round = state.get("current_round", 1)

    logger.info("[Re-reading round %d] Updating codebook...", current_round)

    # Get directory from first document if available
    document_dir = "."
    if documents:
        document_dir = str(documents[0].path.parent)

    @tool
    def read_file(file_name: str, directory: str = document_dir) -> str:
        """Read a document from a file in the specified directory."""
        return read_document_from_file(file_name, directory)

    @tool
    def search_directory(pattern: str, directory: str = document_dir) -> list[str]:
        """Search for a pattern in files within a directory using grep."""
        return grep_search_directory(pattern, directory)

    llm = get_llm_client(model=get_node_model("CREATE_CODEBOOK_MODEL"))

    existing_codebook_str = _codebook_to_str(code_book) if code_book else ""

    system_prompt, user_prompt = get_update_codebook_prompts(
        mode=mode.value,
        user_context=user_context,
        missing_codes_notes=notes,
        existing_codebook_str=existing_codebook_str,
        hierarchy_depth=hierarchy_depth,
    )

    tool_info = """
You have access to the following tools to help update the codebook:
1. read_file(file_name, directory) - Read a specific document file to get more context
2. search_directory(pattern, directory) - Search for patterns in documents to understand patterns better

Use these tools to gather additional context if needed before finalizing the updated codebook.
"""
    enhanced_prompt = tool_info + "\n" + user_prompt

    response_text = await llm.generate_with_tools(
        prompt=enhanced_prompt,
        tools=[read_file, search_directory],
        system_prompt=system_prompt,
    )

    final_prompt = f"""Based on the following analysis, create a valid JSON codebook (including ALL existing codes plus new ones):

{response_text}

Return the complete codebook as a valid JSON object matching the CodeBookSchema."""

    response = await llm.generate_structured(
        prompt=final_prompt,
        schema=CodeBookSchema,
        system_prompt=system_prompt,
    )

    codes = [
        Code(
            name=c["name"],
            description=c["description"],
            criteria=c["criteria"],
            parent_code_name=c.get("parent_code_name"),
        )
        for c in response["codes"]
    ]

    updated_code_book = CodeBook(codes=codes, mode=mode, context=user_context, hierarchy_depth=hierarchy_depth)

    logger.info("[Re-reading round %d] Codebook updated: %d codes", current_round, len(codes))
    for c in codes:
        parent_info = f" (parent: {c.parent_code_name})" if c.parent_code_name else ""
        logger.debug("[Re-reading]   Code: %s%s", c.name, parent_info)

    return {
        "code_book": updated_code_book,
        # Reset for the next round (if any)
        "current_doc_index": 0,
        "notes": "",
        "current_round": current_round + 1,
    }
