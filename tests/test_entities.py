"""Tests for domain entities."""

from pathlib import Path
import pytest

from inductive_coder.domain.entities import (
    AnalysisMode,
    Code,
    CodeBook,
    Document,
    Sentence,
    SentenceCode,
    DocumentCode,
    Chunk,
    AnalysisResult,
)


def test_code_creation() -> None:
    """Test creating a code."""
    code = Code(
        name="Positive Service",
        description="Customer expressed satisfaction with service",
        criteria="Mentions helpful staff or good support",
    )
    
    assert code.name == "Positive Service"
    assert code.description == "Customer expressed satisfaction with service"
    assert "Positive Service" in str(code)


def test_code_book_operations() -> None:
    """Test code book operations."""
    code_book = CodeBook(mode=AnalysisMode.CODING)
    
    assert len(code_book) == 0
    
    code1 = Code(name="Code1", description="First code", criteria="Criteria 1")
    code2 = Code(name="Code2", description="Second code", criteria="Criteria 2")
    
    code_book.add_code(code1)
    code_book.add_code(code2)
    
    assert len(code_book) == 2
    assert code_book.get_code("Code1") == code1
    assert code_book.get_code("Code2") == code2
    assert code_book.get_code("NonExistent") is None


def test_document_parsing() -> None:
    """Test document parsing into sentences."""
    content = "First line.\nSecond line.\n\nThird line."
    path = Path("/tmp/test.txt")
    
    doc = Document(path=path, content=content)
    
    # Should have 3 sentences (empty line is skipped)
    assert len(doc) == 3
    assert doc.sentences[0].text == "First line."
    assert doc.sentences[1].text == "Second line."
    assert doc.sentences[2].text == "Third line."
    
    # Check sentence IDs
    assert doc.sentences[0].id == "test_1"
    assert doc.sentences[1].id == "test_2"
    assert doc.sentences[2].id == "test_4"  # Line 4 because of empty line


def test_sentence_creation() -> None:
    """Test sentence creation."""
    sentence = Sentence(
        id="doc1_5",
        text="This is a test sentence.",
        line_number=5,
        file_path=Path("/tmp/doc1.txt"),
    )
    
    assert sentence.id == "doc1_5"
    assert sentence.text == "This is a test sentence."
    assert sentence.line_number == 5
    assert "doc1_5" in str(sentence)


def test_chunk_creation() -> None:
    """Test chunk creation."""
    sentences = [
        Sentence(id="doc_1", text="Line 1", line_number=1, file_path=Path("/tmp/doc.txt")),
        Sentence(id="doc_2", text="Line 2", line_number=2, file_path=Path("/tmp/doc.txt")),
    ]
    
    chunk = Chunk(
        start_sentence_id="doc_1",
        end_sentence_id="doc_2",
        sentences=sentences,
        should_code=True,
    )
    
    assert len(chunk) == 2
    assert chunk.should_code is True
    assert "doc_1" in str(chunk)


def test_analysis_result_coding_mode() -> None:
    """Test analysis result for coding mode."""
    code_book = CodeBook(mode=AnalysisMode.CODING)
    code = Code(name="TestCode", description="Test", criteria="Test criteria")
    code_book.add_code(code)
    
    result = AnalysisResult(mode=AnalysisMode.CODING, code_book=code_book)
    
    # Add sentence codes
    sc1 = SentenceCode(sentence_id="doc1_1", code=code, rationale="Test rationale")
    sc2 = SentenceCode(sentence_id="doc1_2", code=code)
    
    result.add_sentence_code(sc1)
    result.add_sentence_code(sc2)
    
    assert len(result.sentence_codes) == 2
    
    # Get codes for sentence
    codes_for_s1 = result.get_codes_for_sentence("doc1_1")
    assert len(codes_for_s1) == 1
    assert codes_for_s1[0].sentence_id == "doc1_1"
    
    # Get sentences for code
    sentences_for_code = result.get_sentences_for_code("TestCode")
    assert len(sentences_for_code) == 2


def test_analysis_result_categorization_mode() -> None:
    """Test analysis result for categorization mode."""
    code_book = CodeBook(mode=AnalysisMode.CATEGORIZATION)
    code = Code(name="Category1", description="Test category", criteria="Test criteria")
    code_book.add_code(code)
    
    result = AnalysisResult(mode=AnalysisMode.CATEGORIZATION, code_book=code_book)
    
    # Add document codes
    dc1 = DocumentCode(file_path=Path("/tmp/doc1.txt"), code=code)
    dc2 = DocumentCode(file_path=Path("/tmp/doc2.txt"), code=code)
    
    result.add_document_code(dc1)
    result.add_document_code(dc2)
    
    assert len(result.document_codes) == 2
    
    # Get codes for document
    codes_for_doc1 = result.get_codes_for_document(Path("/tmp/doc1.txt"))
    assert len(codes_for_doc1) == 1
    assert codes_for_doc1[0].file_path == Path("/tmp/doc1.txt")
