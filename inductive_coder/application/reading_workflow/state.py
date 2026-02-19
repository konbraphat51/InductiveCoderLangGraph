"""State definitions for the Reading workflow."""

from pathlib import Path
from typing import TypedDict, Callable, Optional

from inductive_coder.domain.entities import (
    AnalysisMode,
    CodeBook,
    Document,
    HierarchyDepth,
)


class ReadingStateDict(TypedDict):
    """State dict for Reading workflow (LangGraph state)."""
    mode: AnalysisMode
    documents: list[Document]
    user_context: str
    notes: str  # Long-term memory as a single editable text
    current_doc_index: int
    code_book: CodeBook | None
    hierarchy_depth: HierarchyDepth
    progress_callback: Optional[Callable[[str, int, int], None]]
    notes_file_path: Optional[Path]  # Path to write notes in real-time
