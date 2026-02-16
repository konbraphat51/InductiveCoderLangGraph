"""Graph construction for the Categorization workflow."""

import asyncio
import os
from typing import Any

from langgraph.graph import StateGraph, END

from inductive_coder.domain.entities import CodeBook, Document, DocumentCode
from inductive_coder.application.categorization_workflow.state import CategorizationStateDict
from inductive_coder.application.categorization_workflow.nodes import categorize_document_node, categorize_single_document
from inductive_coder.application.categorization_workflow.edges import should_continue_categorization


class CategorizationWorkflow:
    """Wrapper for Categorization workflow."""
    
    def __init__(self, graph: StateGraph) -> None:
        self.app = graph.compile()
    
    async def execute(
        self,
        documents: list[Document],
        code_book: CodeBook,
    ) -> list[DocumentCode]:
        """Execute Categorization workflow with parallel processing."""
        # Get max concurrent requests from environment
        max_concurrent = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Process documents in parallel with rate limiting
        async def process_with_limit(doc: Document) -> list[DocumentCode]:
            async with semaphore:
                return await categorize_single_document(doc, code_book)
        
        # Execute all documents in parallel
        results = await asyncio.gather(
            *[process_with_limit(doc) for doc in documents]
        )
        
        # Flatten results
        document_codes: list[DocumentCode] = []
        for doc_codes in results:
            document_codes.extend(doc_codes)
        
        return document_codes


def create_categorization_workflow() -> CategorizationWorkflow:
    """Create the Categorization workflow graph."""
    
    # Build the graph
    workflow = StateGraph(CategorizationStateDict)
    
    # Add nodes
    workflow.add_node("categorize_document", categorize_document_node)
    
    # Set entry point
    workflow.set_entry_point("categorize_document")
    
    # Add edges
    workflow.add_conditional_edges(
        "categorize_document",
        should_continue_categorization,
        {
            "categorize_document": "categorize_document",
            END: END,
        }
    )
    
    return CategorizationWorkflow(workflow)
