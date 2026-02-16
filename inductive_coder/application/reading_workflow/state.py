"""State definitions for the Reading workflow."""

from typing import Annotated, TypedDict
import operator

from inductive_coder.domain.entities import (
    AnalysisMode,
    CodeBook,
    Document,
)


class ReadingStateDict(TypedDict):
    """State dict for Reading workflow (LangGraph state)."""
    mode: AnalysisMode
    documents: list[Document]
    user_context: str
    notes: Annotated[list[str], operator.add]
    current_doc_index: int
    code_book: CodeBook | None
