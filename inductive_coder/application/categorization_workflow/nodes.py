"""Node functions for the Categorization workflow."""

from typing import Any

from pydantic import BaseModel, Field
from langgraph.types import Send

from inductive_coder.domain.entities import DocumentCode
from inductive_coder.infrastructure.llm_client import get_llm_client, get_node_model
from inductive_coder.application.categorization_workflow.prompts import get_categorize_document_prompts
from inductive_coder.application.categorization_workflow.state import (
    CategorizationStateDict,
    SingleDocCategorizationState,
)


# Pydantic schemas for structured output

class DocumentCodeSchema(BaseModel):
    """Schema for document codes."""
    code_names: list[str] = Field(description="Names of codes to apply to this document")
    rationales: dict[str, str] = Field(
        default_factory=dict,
        description="Rationale for each code (code_name -> rationale)"
    )


# Node functions

def fan_out_documents(state: CategorizationStateDict) -> list[Send]:
    """Fan out to process each document in parallel."""
    sends = []
    for doc in state["documents"]:
        sends.append(
            Send(
                "categorize_single_document",
                {
                    "document": doc,
                    "code_book": state["code_book"],
                    "document_codes": [],
                }
            )
        )
    return sends


async def categorize_single_document(state: SingleDocCategorizationState) -> dict[str, Any]:
    """Categorize a single document."""
    doc = state["document"]
    code_book = state["code_book"]
    
    llm = get_llm_client(model=get_node_model("CATEGORIZE_DOCUMENT_MODEL"))
    
    # Create prompt
    code_list = "\n".join([
        f"- {c.name}: {c.description}\n  Criteria: {c.criteria}"
        for c in code_book.codes
    ])
    
    system_prompt, user_prompt = get_categorize_document_prompts(
        doc_name=doc.path.name,
        doc_content=doc.content,
        code_list=code_list
    )

    response = await llm.generate_structured(
        prompt=user_prompt,
        schema=DocumentCodeSchema,
        system_prompt=system_prompt,
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
    }
