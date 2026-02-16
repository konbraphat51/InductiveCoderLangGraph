"""Node functions for the Categorization workflow."""

from typing import Any

from pydantic import BaseModel, Field

from inductive_coder.domain.entities import DocumentCode
from inductive_coder.infrastructure.llm_client import get_llm_client
from inductive_coder.application.prompts import get_categorize_document_prompt
from inductive_coder.application.categorization_workflow.state import CategorizationStateDict


# Pydantic schemas for structured output

class DocumentCodeSchema(BaseModel):
    """Schema for document codes."""
    code_names: list[str] = Field(description="Names of codes to apply to this document")
    rationales: dict[str, str] = Field(
        default_factory=dict,
        description="Rationale for each code (code_name -> rationale)"
    )


# Node functions

async def categorize_document_node(state: CategorizationStateDict) -> dict[str, Any]:
    """Categorize a single document."""
    current_idx = state["current_doc_index"]
    documents = state["documents"]
    
    if current_idx >= len(documents):
        return {"current_doc_index": current_idx}
    
    doc = documents[current_idx]
    code_book = state["code_book"]
    
    llm = get_llm_client()
    
    # Create prompt
    code_list = "\n".join([
        f"- {c.name}: {c.description}\n  Criteria: {c.criteria}"
        for c in code_book.codes
    ])
    
    prompt = get_categorize_document_prompt(
        doc_name=doc.path.name,
        doc_content=doc.content,
        code_list=code_list
    )

    response = await llm.generate_structured(
        prompt=prompt,
        schema=DocumentCodeSchema,
    )
    
    # Convert to domain entities
    document_codes: list[DocumentCode] = []
    
    for code_name in response["code_names"]:
        code = code_book.get_code(code_name)
        if code:
            rationale = response.get("rationales", {}).get(code_name)
            document_codes.append(
                DocumentCode(
                    file_path=doc.path,
                    code=code,
                    rationale=rationale,
                )
            )
    
    return {
        "document_codes": document_codes,
        "current_doc_index": current_idx + 1,
    }
