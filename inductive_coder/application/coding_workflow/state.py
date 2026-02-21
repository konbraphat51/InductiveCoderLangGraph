"""State definitions for the Coding workflow."""

from typing import Annotated, TypedDict, Callable, Optional
import operator

from inductive_coder.domain.entities import (
    CodeBook,
    Chunk,
    Document,
    SentenceCode,
)


class CodingStateDict(TypedDict):
    """State dict for Coding workflow (LangGraph state)."""
    documents: list[Document]
    code_book: CodeBook
    user_context: str
    sentence_codes: Annotated[list[SentenceCode], operator.add]
    processed_documents: int
    progress_callback: Optional[Callable[[str, int, int], None]]


class SingleDocCodingState(TypedDict):
    """State for processing a single document in parallel."""
    document: Document
    code_book: CodeBook
    user_context: str
    chunks: list[Chunk]
    current_chunk_index: int
    sentence_codes: Annotated[list[SentenceCode], operator.add]
    progress_callback: Optional[Callable[[str, int, int], None]]
