"""State definitions for the Coding workflow."""

from typing import Annotated, TypedDict
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
    current_doc_index: int
    current_doc: Document | None
    chunks: list[Chunk]
    current_chunk_index: int
    sentence_codes: Annotated[list[SentenceCode], operator.add]
