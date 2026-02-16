"""Tests for parallel processing in workflows."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from inductive_coder.domain.entities import (
    AnalysisMode,
    Code,
    CodeBook,
    Document,
    DocumentCode,
    Sentence,
    SentenceCode,
)
from inductive_coder.application.categorization_workflow.graph import create_categorization_workflow
from inductive_coder.application.coding_workflow.graph import create_coding_workflow


@pytest.fixture
def sample_code_book() -> CodeBook:
    """Create a sample code book for testing."""
    code_book = CodeBook(mode=AnalysisMode.CODING)
    code_book.codes = [
        Code(
            name="Positive",
            description="Positive sentiment",
            criteria="Mentions satisfaction or happiness",
        ),
        Code(
            name="Negative",
            description="Negative sentiment",
            criteria="Mentions dissatisfaction or problems",
        ),
    ]
    return code_book


@pytest.fixture
def sample_documents() -> list[Document]:
    """Create sample documents for testing."""
    docs = []
    for i in range(3):
        doc = Document(
            path=Path(f"test_doc_{i}.txt"),
            content=f"This is test sentence 1 in document {i}.\nThis is test sentence 2 in document {i}.",
            sentences=[
                Sentence(
                    id=f"test_doc_{i}_0",
                    text=f"This is test sentence 1 in document {i}.",
                    line_number=0,
                    file_path=Path(f"test_doc_{i}.txt"),
                ),
                Sentence(
                    id=f"test_doc_{i}_1",
                    text=f"This is test sentence 2 in document {i}.",
                    line_number=1,
                    file_path=Path(f"test_doc_{i}.txt"),
                ),
            ],
        )
        docs.append(doc)
    return docs


@pytest.mark.asyncio
async def test_categorization_parallel_processing(
    sample_documents: list[Document],
    sample_code_book: CodeBook,
) -> None:
    """Test that categorization workflow processes documents in parallel."""
    
    # Track call order to verify parallelism
    call_order = []
    call_lock = asyncio.Lock()
    
    async def mock_categorize_single_document(doc: Document, code_book: CodeBook) -> list[DocumentCode]:
        """Mock function that tracks call order."""
        async with call_lock:
            call_order.append(("start", doc.path.name))
        
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        async with call_lock:
            call_order.append(("end", doc.path.name))
        
        # Return a mock result
        return [
            DocumentCode(
                file_path=doc.path,
                code=sample_code_book.codes[0],
                rationale="Test rationale",
            )
        ]
    
    # Patch the categorize_single_document function
    with patch(
        "inductive_coder.application.categorization_workflow.graph.categorize_single_document",
        side_effect=mock_categorize_single_document,
    ):
        workflow = create_categorization_workflow()
        
        start_time = asyncio.get_event_loop().time()
        result = await workflow.execute(
            documents=sample_documents,
            code_book=sample_code_book,
        )
        end_time = asyncio.get_event_loop().time()
    
    # Verify results
    assert len(result) == 3, "Should return codes for all 3 documents"
    
    # Verify parallel execution
    # If sequential, would take ~0.3s (3 * 0.1s)
    # If parallel, should take ~0.1s
    elapsed_time = end_time - start_time
    assert elapsed_time < 0.25, f"Expected parallel execution (< 0.25s), but took {elapsed_time:.2f}s"
    
    # Verify that all documents started before any finished (indicating parallelism)
    start_events = [event for event in call_order if event[0] == "start"]
    end_events = [event for event in call_order if event[0] == "end"]
    
    # All starts should come before at least some ends if parallel
    first_end_index = call_order.index(end_events[0])
    assert len([e for e in call_order[:first_end_index] if e[0] == "start"]) > 1, \
        "Expected multiple documents to start processing before first one finishes (parallel execution)"


@pytest.mark.asyncio
async def test_coding_parallel_processing(
    sample_documents: list[Document],
    sample_code_book: CodeBook,
) -> None:
    """Test that coding workflow processes documents in parallel."""
    
    # Track call order to verify parallelism
    call_order = []
    call_lock = asyncio.Lock()
    
    async def mock_process_single_document(doc: Document, code_book: CodeBook) -> list[SentenceCode]:
        """Mock function that tracks call order."""
        async with call_lock:
            call_order.append(("start", doc.path.name))
        
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        async with call_lock:
            call_order.append(("end", doc.path.name))
        
        # Return a mock result
        return [
            SentenceCode(
                sentence_id=doc.sentences[0].id,
                code=sample_code_book.codes[0],
                rationale="Test rationale",
            )
        ]
    
    # Patch the process_single_document function
    with patch(
        "inductive_coder.application.coding_workflow.graph.process_single_document",
        side_effect=mock_process_single_document,
    ):
        workflow = create_coding_workflow()
        
        start_time = asyncio.get_event_loop().time()
        result = await workflow.execute(
            documents=sample_documents,
            code_book=sample_code_book,
        )
        end_time = asyncio.get_event_loop().time()
    
    # Verify results
    assert len(result) == 3, "Should return codes for all 3 documents"
    
    # Verify parallel execution
    # If sequential, would take ~0.3s (3 * 0.1s)
    # If parallel, should take ~0.1s
    elapsed_time = end_time - start_time
    assert elapsed_time < 0.25, f"Expected parallel execution (< 0.25s), but took {elapsed_time:.2f}s"
    
    # Verify that all documents started before any finished (indicating parallelism)
    start_events = [event for event in call_order if event[0] == "start"]
    end_events = [event for event in call_order if event[0] == "end"]
    
    # All starts should come before at least some ends if parallel
    first_end_index = call_order.index(end_events[0])
    assert len([e for e in call_order[:first_end_index] if e[0] == "start"]) > 1, \
        "Expected multiple documents to start processing before first one finishes (parallel execution)"


@pytest.mark.asyncio
async def test_rate_limiting_respects_max_concurrent_requests(
    sample_documents: list[Document],
    sample_code_book: CodeBook,
) -> None:
    """Test that rate limiting respects MAX_CONCURRENT_REQUESTS."""
    
    # Track concurrent executions
    concurrent_count = 0
    max_concurrent_seen = 0
    count_lock = asyncio.Lock()
    
    async def mock_categorize_with_tracking(doc: Document, code_book: CodeBook) -> list[DocumentCode]:
        """Mock function that tracks concurrent executions."""
        nonlocal concurrent_count, max_concurrent_seen
        
        async with count_lock:
            concurrent_count += 1
            if concurrent_count > max_concurrent_seen:
                max_concurrent_seen = concurrent_count
        
        # Simulate API delay
        await asyncio.sleep(0.05)
        
        async with count_lock:
            concurrent_count -= 1
        
        return [
            DocumentCode(
                file_path=doc.path,
                code=sample_code_book.codes[0],
                rationale="Test",
            )
        ]
    
    # Create more documents to test concurrency limit
    many_docs = sample_documents * 3  # 9 documents total
    
    # Test with MAX_CONCURRENT_REQUESTS=3
    with patch(
        "inductive_coder.application.categorization_workflow.graph.categorize_single_document",
        side_effect=mock_categorize_with_tracking,
    ), patch.dict("os.environ", {"MAX_CONCURRENT_REQUESTS": "3"}):
        workflow = create_categorization_workflow()
        result = await workflow.execute(
            documents=many_docs,
            code_book=sample_code_book,
        )
    
    # Verify that we never exceeded the limit
    assert max_concurrent_seen <= 3, \
        f"Expected max concurrent requests <= 3, but saw {max_concurrent_seen}"
    
    # Verify results
    assert len(result) == 9, "Should return codes for all 9 documents"
