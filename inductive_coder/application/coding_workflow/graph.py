"""Graph construction for the Coding workflow."""

from typing import Any

from langgraph.graph import StateGraph, END

from inductive_coder.domain.entities import CodeBook, Document, SentenceCode
from inductive_coder.application.coding_workflow.state import CodingStateDict
from inductive_coder.application.coding_workflow.nodes import (
    decide_chunking_node,
    code_chunk_node,
    next_document_node,
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
        """Execute Coding workflow."""
        initial_state: CodingStateDict = {
            "documents": documents,
            "code_book": code_book,
            "current_doc_index": 0,
            "current_doc": None,
            "chunks": [],
            "current_chunk_index": 0,
            "sentence_codes": [],
        }
        
        result = await self.app.ainvoke(initial_state)
        return result["sentence_codes"]


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
