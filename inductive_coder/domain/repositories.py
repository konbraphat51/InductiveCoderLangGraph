"""Repository interfaces (ports) for the domain layer."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from inductive_coder.domain.entities import (
    AnalysisResult,
    CodeBook,
    Document,
)


class IDocumentRepository(ABC):
    """Interface for document repository."""
    
    @abstractmethod
    def load_document(self, path: Path) -> Document:
        """Load a single document from a file."""
        pass
    
    @abstractmethod
    def load_documents(self, directory: Path) -> list[Document]:
        """Load all documents from a directory."""
        pass
    
    @abstractmethod
    def save_document(self, document: Document, output_path: Path) -> None:
        """Save a document to a file."""
        pass


class ICodeBookRepository(ABC):
    """Interface for code book repository."""
    
    @abstractmethod
    def save_code_book(self, code_book: CodeBook, path: Path) -> None:
        """Save a code book to a file."""
        pass
    
    @abstractmethod
    def load_code_book(self, path: Path) -> CodeBook:
        """Load a code book from a file."""
        pass


class IAnalysisResultRepository(ABC):
    """Interface for analysis result repository."""
    
    @abstractmethod
    def save_result(self, result: AnalysisResult, output_dir: Path) -> None:
        """Save analysis results to output directory."""
        pass
    
    @abstractmethod
    def load_result(self, output_dir: Path) -> AnalysisResult:
        """Load analysis results from output directory."""
        pass


class ILLMClient(ABC):
    """Interface for LLM client."""
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def generate_structured(
        self, 
        prompt: str, 
        schema: type,
        system_prompt: Optional[str] = None
    ) -> dict:
        """Generate a structured response matching the given schema."""
        pass
