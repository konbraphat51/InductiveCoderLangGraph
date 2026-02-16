"""Tests for repository implementations."""

import json
from pathlib import Path
import pytest
import tempfile

from inductive_coder.domain.entities import (
    AnalysisMode,
    Code,
    CodeBook,
    Document,
    SentenceCode,
    DocumentCode,
    AnalysisResult,
)
from inductive_coder.infrastructure.repositories import (
    FileSystemDocumentRepository,
    JSONCodeBookRepository,
    JSONAnalysisResultRepository,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_load_document(temp_dir: Path) -> None:
    """Test loading a single document."""
    # Create a test file
    test_file = temp_dir / "test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3", encoding="utf-8")
    
    repo = FileSystemDocumentRepository()
    doc = repo.load_document(test_file)
    
    assert doc.path == test_file
    assert "Line 1" in doc.content
    assert len(doc.sentences) == 3


def test_load_documents(temp_dir: Path) -> None:
    """Test loading multiple documents."""
    # Create test files
    (temp_dir / "doc1.txt").write_text("Content 1", encoding="utf-8")
    (temp_dir / "doc2.md").write_text("Content 2", encoding="utf-8")
    (temp_dir / "ignored.py").write_text("Ignored", encoding="utf-8")
    
    repo = FileSystemDocumentRepository()
    docs = repo.load_documents(temp_dir)
    
    # Should load .txt and .md files, not .py
    assert len(docs) == 2
    assert any(d.path.name == "doc1.txt" for d in docs)
    assert any(d.path.name == "doc2.md" for d in docs)


def test_save_and_load_code_book(temp_dir: Path) -> None:
    """Test saving and loading a code book."""
    # Create code book
    code_book = CodeBook(mode=AnalysisMode.CODING, context="Test context")
    code_book.add_code(Code(name="Code1", description="Desc 1", criteria="Criteria 1"))
    code_book.add_code(Code(name="Code2", description="Desc 2", criteria="Criteria 2"))
    
    # Save
    repo = JSONCodeBookRepository()
    save_path = temp_dir / "codebook.json"
    repo.save_code_book(code_book, save_path)
    
    assert save_path.exists()
    
    # Load
    loaded = repo.load_code_book(save_path)
    
    assert loaded.mode == AnalysisMode.CODING
    assert loaded.context == "Test context"
    assert len(loaded.codes) == 2
    assert loaded.get_code("Code1") is not None
    assert loaded.get_code("Code1").description == "Desc 1"


def test_save_coding_result(temp_dir: Path) -> None:
    """Test saving coding mode results."""
    # Create result
    code_book = CodeBook(mode=AnalysisMode.CODING)
    code = Code(name="TestCode", description="Test", criteria="Test criteria")
    code_book.add_code(code)
    
    result = AnalysisResult(mode=AnalysisMode.CODING, code_book=code_book)
    result.add_sentence_code(SentenceCode(
        sentence_id="doc1_1",
        code=code,
        rationale="Test rationale"
    ))
    
    # Save
    repo = JSONAnalysisResultRepository()
    repo.save_result(result, temp_dir)
    
    # Check files exist
    assert (temp_dir / "code_book.json").exists()
    assert (temp_dir / "sentence_codes.json").exists()
    assert (temp_dir / "summary.txt").exists()
    
    # Check content
    with (temp_dir / "sentence_codes.json").open("r") as f:
        data = json.load(f)
    
    assert data["mode"] == "coding"
    assert "TestCode" in data["codes_by_name"]


def test_save_categorization_result(temp_dir: Path) -> None:
    """Test saving categorization mode results."""
    # Create result
    code_book = CodeBook(mode=AnalysisMode.CATEGORIZATION)
    code = Code(name="Category1", description="Test category", criteria="Test criteria")
    code_book.add_code(code)
    
    result = AnalysisResult(mode=AnalysisMode.CATEGORIZATION, code_book=code_book)
    result.add_document_code(DocumentCode(
        file_path=Path("/tmp/doc1.txt"),
        code=code,
        rationale="Test rationale"
    ))
    
    # Save
    repo = JSONAnalysisResultRepository()
    repo.save_result(result, temp_dir)
    
    # Check files exist
    assert (temp_dir / "code_book.json").exists()
    assert (temp_dir / "document_codes.json").exists()
    assert (temp_dir / "summary.txt").exists()
    
    # Check content
    with (temp_dir / "document_codes.json").open("r") as f:
        data = json.load(f)
    
    assert data["mode"] == "categorization"
    assert "Category1" in data["codes_by_name"]


def test_save_and_load_hierarchical_code_book(temp_dir: Path) -> None:
    """Test saving and loading a hierarchical code book."""
    from inductive_coder.domain.entities import HierarchyDepth
    
    # Create hierarchical code book
    code_book = CodeBook(
        mode=AnalysisMode.CODING,
        context="Test hierarchical context",
        hierarchy_depth=HierarchyDepth.TWO_LEVEL
    )
    
    # Add parent and child codes
    parent = Code(name="Parent", description="Parent code", criteria="Parent criteria")
    child = Code(
        name="Child",
        description="Child code",
        criteria="Child criteria",
        parent_code_name="Parent"
    )
    
    code_book.add_code(parent)
    code_book.add_code(child)
    
    # Save
    repo = JSONCodeBookRepository()
    save_path = temp_dir / "hierarchical_codebook.json"
    repo.save_code_book(code_book, save_path)
    
    assert save_path.exists()
    
    # Verify JSON structure
    with save_path.open("r") as f:
        data = json.load(f)
    
    assert data["hierarchy_depth"] == "2"
    assert len(data["codes"]) == 2
    assert data["codes"][0]["parent_code_name"] is None
    assert data["codes"][1]["parent_code_name"] == "Parent"
    
    # Load
    loaded = repo.load_code_book(save_path)
    
    assert loaded.mode == AnalysisMode.CODING
    assert loaded.context == "Test hierarchical context"
    assert loaded.hierarchy_depth == HierarchyDepth.TWO_LEVEL
    assert len(loaded.codes) == 2
    
    # Verify hierarchy
    root_codes = loaded.get_root_codes()
    assert len(root_codes) == 1
    assert root_codes[0].name == "Parent"
    
    children = loaded.get_children("Parent")
    assert len(children) == 1
    assert children[0].name == "Child"
    assert children[0].parent_code_name == "Parent"
