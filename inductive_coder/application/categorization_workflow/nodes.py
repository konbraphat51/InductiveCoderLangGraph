"""Node functions for the Categorization workflow."""

from typing import Any

from pydantic import BaseModel, Field

from inductive_coder.domain.entities import DocumentCode
from inductive_coder.infrastructure.llm_client import get_llm_client, get_node_model
from inductive_coder.application.categorization_workflow.prompts import get_categorize_document_prompts
from inductive_coder.application.categorization_workflow.state import (
    SingleDocCategorizationState,
)
from inductive_coder.logger import logger


# Pydantic schemas for structured output

class DocumentCodeEntrySchema(BaseModel):
    """Schema for a single document code assignment."""
    code_name: str = Field(description="Name of the code to apply")
    rationale: str = Field(default="", description="Why this code applies to the document")


class DocumentCodeSchema(BaseModel):
    """Schema for document codes."""
    codes: list[DocumentCodeEntrySchema] = Field(
        default_factory=list,
        description="List of codes to apply to this document, each with a rationale"
    )


# Node functions

async def categorize_single_document(state: SingleDocCategorizationState) -> dict[str, Any]:
    """Categorize a single document."""
    doc = state["document"]
    code_book = state["code_book"]
    user_context = state["user_context"]
    progress_callback = state.get("progress_callback")
    
    logger.info("[Categorization] Start: %s", doc.path.name)
    
    llm = get_llm_client(model=get_node_model("CATEGORIZE_DOCUMENT_MODEL"))
    
    # Create prompt
    code_list = "\n".join([
        f"- {c.name}: {c.description}\n  Criteria: {c.criteria}"
        for c in code_book.codes
    ])
    
    system_prompt, user_prompt = get_categorize_document_prompts(
        doc_name=doc.path.name,
        doc_content=doc.content,
        code_list=code_list,
        user_context=user_context
    )

    response = await llm.generate_structured(
        prompt=user_prompt,
        schema=DocumentCodeSchema,
        system_prompt=system_prompt,
    )
    
    # Convert to domain entities
    document_codes: list[DocumentCode] = []
    
    for entry in response["codes"]:
        code = code_book.get_code(entry["code_name"])
        if code:
            document_codes.append(
                DocumentCode(
                    file_path=doc.path,
                    code=code,
                    rationale=entry.get("rationale") or None,
                )
            )
    
    assigned = [dc.code.name for dc in document_codes]
    logger.info("[Categorization] Done:  %s -> [%s]", doc.path.name, ", ".join(assigned))
    
    if progress_callback:
        progress_callback("Categorization", 1, 1)  # absolute count tracked in use_case
    
    return {
        "document_codes": document_codes,
    }
