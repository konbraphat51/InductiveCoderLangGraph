"""Graph construction for the Coding workflow."""

import asyncio
import os
from typing import Any

from langgraph.graph import StateGraph, END

from inductive_coder.domain.entities import CodeBook, Document, SentenceCode
from inductive_coder.application.coding_workflow.state import CodingStateDict
from inductive_coder.application.coding_workflow.nodes import (
    decide_chunking_node,
    code_chunk_node,
    next_document_node,
    process_single_document,
)
from inductive_coder.application.coding_workflow.edges import (
    should_continue_coding_chunks,
    should_continue_coding_documents,
)


class CodingWorkflow:
    """Wrapper for Coding workflow."""
    
    def __init__(self, graph: StateGraph) -> None:
        self.app = graph.compile()
    
    async def execute(
        self,
        documents: list[Document],
        code_book: CodeBook,
    ) -> list[SentenceCode]:
        """Execute Coding workflow with parallel processing."""
        # Get max concurrent requests from environment
        max_concurrent = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Process documents in parallel with rate limiting
        async def process_with_limit(doc: Document) -> list[SentenceCode]:
            async with semaphore:
                return await process_single_document(doc, code_book)
        
        # Execute all documents in parallel
        results = await asyncio.gather(
            *[process_with_limit(doc) for doc in documents]
        )
        
        # Flatten results
        sentence_codes: list[SentenceCode] = []
        for doc_codes in results:
            sentence_codes.extend(doc_codes)
        
        return sentence_codes


def create_coding_workflow() -> CodingWorkflow:
    """Create the Coding workflow graph."""
    
    # Build the graph
    workflow = StateGraph(CodingStateDict)
    
    # Add nodes
    workflow.add_node("decide_chunking", decide_chunking_node)
    workflow.add_node("code_chunk", code_chunk_node)
    workflow.add_node("next_document", next_document_node)
    
    # Set entry point
    workflow.set_entry_point("decide_chunking")
    
    # Add edges
    workflow.add_conditional_edges(
        "code_chunk",
        should_continue_coding_chunks,
        {
            "code_chunk": "code_chunk",
            "next_document": "next_document",
        }
    )
    
    workflow.add_conditional_edges(
        "next_document",
        should_continue_coding_documents,
        {
            "decide_chunking": "decide_chunking",
            END: END,
        }
    )
    
    workflow.add_edge("decide_chunking", "code_chunk")
    
    return CodingWorkflow(workflow)
