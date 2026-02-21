"""State definitions for the Categorization workflow."""

from typing import Annotated, TypedDict, Callable, Optional
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
    user_context: str
    document_codes: Annotated[list[DocumentCode], operator.add]
    processed_documents: int
    progress_callback: Optional[Callable[[str, int, int], None]]


class SingleDocCategorizationState(TypedDict):
    """State for processing a single document in parallel."""
    document: Document
    code_book: CodeBook
    user_context: str
    document_codes: Annotated[list[DocumentCode], operator.add]
    progress_callback: Optional[Callable[[str, int, int], None]]
