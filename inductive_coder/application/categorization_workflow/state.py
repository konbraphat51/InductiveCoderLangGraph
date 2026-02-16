"""State definitions for the Categorization workflow."""

from typing import Annotated, TypedDict
import operator

from inductive_coder.domain.entities import (
    CodeBook,
    Document,
    DocumentCode,
)


class CategorizationStateDict(TypedDict):
    """State dict for Categorization workflow (LangGraph state)."""
    documents: list[Document]
    code_book: CodeBook
    current_doc_index: int
    document_codes: Annotated[list[DocumentCode], operator.add]
