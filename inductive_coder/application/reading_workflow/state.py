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
    notes: str  # Long-term memory as a single editable text (initial reading only)
    re_reading_notes: list[str]  # Accumulated missing-code notes per doc/batch during re-reading
    current_doc_index: int
    code_book: CodeBook | None
    hierarchy_depth: HierarchyDepth
    batch_size: int  # Number of documents to read per LLM call
    progress_callback: Optional[Callable[[str, int, int], None]]
    notes_file_path: Optional[Path]  # Path to write notes in real-time
    re_reading_rounds: int  # Number of additional re-reading rounds (0 = no re-reading)
    current_round: int  # Current round number (0 = initial reading, 1+ = re-reading)
