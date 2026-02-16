"""Domain entities for the inductive coding system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from pathlib import Path


class AnalysisMode(str, Enum):
    """Analysis mode for inductive coding."""
    
    CODING = "coding"
    CATEGORIZATION = "categorization"


class HierarchyDepth(str, Enum):
    """Hierarchy depth for code structure."""
    
    FLAT = "1"  # No hierarchy
    TWO_LEVEL = "2"  # Maximum 2 levels (parent-child)
    ARBITRARY = "arbitrary"  # Unlimited depth (LLM decides)


@dataclass(frozen=True)
class Sentence:
    """A single sentence with an ID in a document."""
    
    id: str  # Format: "filename_line_number"
    text: str
    line_number: int
    file_path: Path
    
    def __str__(self) -> str:
        return f"[{self.id}] {self.text}"


@dataclass(frozen=True)
class Code:
    """A code that can be applied to sentences or documents."""
    
    name: str
    description: str
    criteria: str  # When to apply this code
    parent_code_name: Optional[str] = None  # Name of parent code for hierarchical structure
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


@dataclass(frozen=True)
class SentenceCode:
    """A code applied to a specific sentence."""
    
    sentence_id: str
    code: Code
    rationale: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.sentence_id} -> {self.code.name}"


@dataclass(frozen=True)
class DocumentCode:
    """A code applied to an entire document."""
    
    file_path: Path
    code: Code
    rationale: Optional[str] = None
    
    def __str__(self) -> str:
        return f"{self.file_path.name} -> {self.code.name}"


@dataclass
class CodeBook:
    """A collection of codes with their definitions and criteria."""
    
    codes: list[Code] = field(default_factory=list)
    mode: AnalysisMode = AnalysisMode.CODING
    context: str = ""  # User's research question/context
    hierarchy_depth: HierarchyDepth = HierarchyDepth.FLAT
    
    def add_code(self, code: Code) -> None:
        """Add a code to the code book."""
        self.codes.append(code)
    
    def get_code(self, name: str) -> Optional[Code]:
        """Retrieve a code by name."""
        for code in self.codes:
            if code.name == name:
                return code
        return None
    
    def get_children(self, parent_name: str) -> list[Code]:
        """Get all codes that are children of the specified parent code."""
        return [code for code in self.codes if code.parent_code_name == parent_name]
    
    def get_root_codes(self) -> list[Code]:
        """Get all codes with no parent (top-level codes)."""
        return [code for code in self.codes if code.parent_code_name is None]
    
    def __len__(self) -> int:
        return len(self.codes)
    
    def __str__(self) -> str:
        return f"CodeBook({len(self.codes)} codes, mode={self.mode.value})"


@dataclass
class Document:
    """A document to be analyzed."""
    
    path: Path
    content: str
    sentences: list[Sentence] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Parse content into sentences if not already done."""
        if not self.sentences and self.content:
            self._parse_sentences()
    
    def _parse_sentences(self) -> None:
        """Parse document content into sentences with IDs."""
        lines = self.content.split('\n')
        sentence_id_base = self.path.stem
        
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if line:  # Skip empty lines
                sentence_id = f"{sentence_id_base}_{line_num}"
                sentence = Sentence(
                    id=sentence_id,
                    text=line,
                    line_number=line_num,
                    file_path=self.path
                )
                self.sentences.append(sentence)
    
    def __len__(self) -> int:
        return len(self.sentences)
    
    def __str__(self) -> str:
        return f"Document({self.path.name}, {len(self.sentences)} sentences)"


@dataclass(frozen=True)
class Chunk:
    """A chunk of sentences for processing."""
    
    start_sentence_id: str
    end_sentence_id: str
    sentences: list[Sentence]
    should_code: bool = True  # Whether this chunk is relevant for coding
    
    def __len__(self) -> int:
        return len(self.sentences)
    
    def __str__(self) -> str:
        status = "relevant" if self.should_code else "irrelevant"
        return f"Chunk[{self.start_sentence_id}:{self.end_sentence_id}] ({len(self)} sentences, {status})"


@dataclass
class AnalysisResult:
    """Result of an analysis (coding or categorization)."""
    
    mode: AnalysisMode
    code_book: CodeBook
    sentence_codes: list[SentenceCode] = field(default_factory=list)
    document_codes: list[DocumentCode] = field(default_factory=list)
    
    def add_sentence_code(self, sentence_code: SentenceCode) -> None:
        """Add a sentence-level code."""
        self.sentence_codes.append(sentence_code)
    
    def add_document_code(self, document_code: DocumentCode) -> None:
        """Add a document-level code."""
        self.document_codes.append(document_code)
    
    def get_codes_for_sentence(self, sentence_id: str) -> list[SentenceCode]:
        """Get all codes applied to a specific sentence."""
        return [sc for sc in self.sentence_codes if sc.sentence_id == sentence_id]
    
    def get_codes_for_document(self, file_path: Path) -> list[DocumentCode]:
        """Get all codes applied to a specific document."""
        return [dc for dc in self.document_codes if dc.file_path == file_path]
    
    def get_sentences_for_code(self, code_name: str) -> list[SentenceCode]:
        """Get all sentences with a specific code."""
        return [sc for sc in self.sentence_codes if sc.code.name == code_name]
    
    def __str__(self) -> str:
        if self.mode == AnalysisMode.CODING:
            return f"AnalysisResult(CODING: {len(self.sentence_codes)} coded sentences)"
        else:
            return f"AnalysisResult(CATEGORIZATION: {len(self.document_codes)} coded documents)"
