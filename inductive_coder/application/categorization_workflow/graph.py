"""Graph construction for the Categorization workflow."""

from typing import Any, Optional, Callable

from langgraph.graph import StateGraph, END

from inductive_coder.domain.entities import CodeBook, Document, DocumentCode
from inductive_coder.application.categorization_workflow.state import (
    CategorizationStateDict,
    SingleDocCategorizationState,
)
from inductive_coder.application.categorization_workflow.nodes import (
    fan_out_documents,
    categorize_single_document,
)


class CategorizationWorkflow:
    """Wrapper for Categorization workflow."""
    
    def __init__(self, graph: StateGraph) -> None:
        self.app = graph.compile()
    
    async def execute(
        self,
        documents: list[Document],
        code_book: CodeBook,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> list[DocumentCode]:
        """Execute Categorization workflow."""
        initial_state: CategorizationStateDict = {
            "documents": documents,
            "code_book": code_book,
            "document_codes": [],
            "processed_documents": 0,
            "progress_callback": progress_callback,
        }
        
        result = await self.app.ainvoke(initial_state)
        return result["document_codes"]


def create_categorization_workflow() -> CategorizationWorkflow:
    """Create the Categorization workflow graph."""
    
    # Build the graph
    workflow = StateGraph(CategorizationStateDict)
    
    # Add nodes
    workflow.add_node("fan_out", fan_out_documents)
    workflow.add_node("categorize_single_document", categorize_single_document)
    
    # Set entry point
    workflow.set_entry_point("fan_out")
    
    # Add edges - fan_out sends to categorize_single_document in parallel
    workflow.add_conditional_edges("fan_out", lambda x: x)
    workflow.add_edge("categorize_single_document", END)
    
    return CategorizationWorkflow(workflow)
