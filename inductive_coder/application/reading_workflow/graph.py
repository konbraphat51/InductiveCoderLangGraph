"""Graph construction for the Reading workflow."""

from pathlib import Path
from typing import Any, Optional, Callable

from langgraph.graph import StateGraph, END

from inductive_coder.domain.entities import AnalysisMode, CodeBook, Document, HierarchyDepth
from inductive_coder.application.reading_workflow.state import ReadingStateDict
from inductive_coder.application.reading_workflow.nodes import (
    read_document_node,
    create_codebook_node,
    re_read_document_node,
    update_codebook_node,
)
from inductive_coder.application.reading_workflow.edges import (
    should_continue_reading,
    should_start_re_reading,
    should_continue_re_reading,
    should_continue_rounds,
)


class ReadingWorkflow:
    """Wrapper for Reading workflow."""
    
    def __init__(self, graph: StateGraph[ReadingStateDict]) -> None:
        self.app = graph.compile()
    
    async def execute(
        self,
        mode: AnalysisMode,
        documents: list[Document],
        user_context: str,
        hierarchy_depth: HierarchyDepth = HierarchyDepth.FLAT,
        batch_size: int = 1,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        notes_file_path: Optional[Path] = None,
        re_reading_rounds: int = 0,
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
            "batch_size": batch_size,
            "progress_callback": progress_callback,
            "notes_file_path": notes_file_path,
            "re_reading_rounds": re_reading_rounds,
            "current_round": 1,  # Will be used for re-reading; initial reading is round 0
        }
        
        result = await self.app.ainvoke(initial_state)
        return result["code_book"]



def create_reading_workflow() -> ReadingWorkflow:
    """Create the Reading workflow graph."""
    
    # Build the graph
    workflow = StateGraph[ReadingStateDict](ReadingStateDict)
    
    # Add nodes
    workflow.add_node("read_document", read_document_node)
    workflow.add_node("create_codebook", create_codebook_node)
    workflow.add_node("re_read_document", re_read_document_node)
    workflow.add_node("update_codebook", update_codebook_node)
    
    # Set entry point
    workflow.set_entry_point("read_document")
    
    # Initial reading edges
    workflow.add_conditional_edges(
        "read_document",
        should_continue_reading,
        {
            "read_document": "read_document",
            "create_codebook": "create_codebook",
        }
    )
    
    # After creating codebook: optionally start re-reading rounds
    workflow.add_conditional_edges(
        "create_codebook",
        should_start_re_reading,
        {
            "re_read_document": "re_read_document",
            "__end__": END,
        }
    )
    
    # Re-reading edges
    workflow.add_conditional_edges(
        "re_read_document",
        should_continue_re_reading,
        {
            "re_read_document": "re_read_document",
            "update_codebook": "update_codebook",
        }
    )
    
    # After updating codebook: loop to next re-reading round or finish
    workflow.add_conditional_edges(
        "update_codebook",
        should_continue_rounds,
        {
            "re_read_document": "re_read_document",
            "__end__": END,
        }
    )
    
    return ReadingWorkflow(workflow)
