"""State definitions for LangGraph workflows."""

from dataclasses import dataclass, field
from typing import Optional

from inductive_coder.domain.entities import (
    AnalysisMode,
    Code,
    CodeBook,
    Document,
    Chunk,
    SentenceCode,
    DocumentCode,
)


@dataclass
class ReadingState:
    """State for Round 1: Reading and note-taking."""
    
    mode: AnalysisMode
    documents: list[Document]
    user_context: str
    
    # Accumulated notes
    notes: list[str] = field(default_factory=list)
    current_doc_index: int = 0
    
    # Output
    code_book: Optional[CodeBook] = None


@dataclass
class CodingState:
    """State for Round 2: Coding mode."""
    
    documents: list[Document]
    code_book: CodeBook
    
    # Processing state
    current_doc_index: int = 0
    current_doc: Optional[Document] = None
    chunks: list[Chunk] = field(default_factory=list)
    current_chunk_index: int = 0
    
    # Outputs
    sentence_codes: list[SentenceCode] = field(default_factory=list)


@dataclass
class CategorizationState:
    """State for Round 2: Categorization mode."""
    
    documents: list[Document]
    code_book: CodeBook
    
    # Processing state
    current_doc_index: int = 0
    
    # Outputs
    document_codes: list[DocumentCode] = field(default_factory=list)
