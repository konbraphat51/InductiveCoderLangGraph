"""Graph construction for the Reading workflow."""

from typing import Any

from langgraph.graph import StateGraph, END

from inductive_coder.domain.entities import AnalysisMode, CodeBook, Document, HierarchyDepth
from inductive_coder.application.reading_workflow.state import ReadingStateDict
from inductive_coder.application.reading_workflow.nodes import (
    read_document_node,
    create_codebook_node,
)
from inductive_coder.application.reading_workflow.edges import should_continue_reading


class ReadingWorkflow:
    """Wrapper for Reading workflow."""
    
    def __init__(self, graph: StateGraph) -> None:
        self.app = graph.compile()
    
    async def execute(
        self,
        mode: AnalysisMode,
        documents: list[Document],
        user_context: str,
        hierarchy_depth: HierarchyDepth = HierarchyDepth.FLAT,
    ) -> CodeBook:
        """Execute Reading workflow."""
        initial_state: ReadingStateDict = {
            "mode": mode,
            "documents": documents,
            "user_context": user_context,
            "notes": "",  # Start with empty long-term memory
            "current_doc_index": 0,
            "code_book": None,
            "hierarchy_depth": hierarchy_depth,
        }
        
        result = await self.app.ainvoke(initial_state)
        return result["code_book"]


def create_reading_workflow() -> ReadingWorkflow:
    """Create the Reading workflow graph."""
    
    # Build the graph
    workflow = StateGraph(ReadingStateDict)
    
    # Add nodes
    workflow.add_node("read_document", read_document_node)
    workflow.add_node("create_codebook", create_codebook_node)
    
    # Set entry point
    workflow.set_entry_point("read_document")
    
    # Add edges
    workflow.add_conditional_edges(
        "read_document",
        should_continue_reading,
        {
            "read_document": "read_document",
            "create_codebook": "create_codebook",
        }
    )
    
    workflow.add_edge("create_codebook", END)
    
    return ReadingWorkflow(workflow)
