"""Graph construction for the Categorization workflow."""

from typing import Any, Optional, Callable

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from inductive_coder.domain.entities import CodeBook, Document, DocumentCode
from inductive_coder.application.categorization_workflow.state import (
    CategorizationStateDict,
    SingleDocCategorizationState,
)
from inductive_coder.application.categorization_workflow.nodes import (
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
        user_context: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> list[DocumentCode]:
        """Execute Categorization workflow."""
        initial_state: CategorizationStateDict = {
            "documents": documents,
            "code_book": code_book,
            "user_context": user_context,
            "document_codes": [],
            "processed_documents": 0,
            "progress_callback": progress_callback,
        }
        
        result = await self.app.ainvoke(initial_state)
        return result["document_codes"]


def fan_out_mapper(state: CategorizationStateDict):
    """Route each document to categorize_single_document in parallel."""
    return [
        Send(
            "categorize_single_document",
            {
                "document": doc,
                "code_book": state["code_book"],
                "user_context": state["user_context"],
                "document_codes": [],
                "progress_callback": state.get("progress_callback"),
            }
        )
        for doc in state["documents"]
    ]


def create_categorization_workflow() -> CategorizationWorkflow:
    """Create the Categorization workflow graph."""
    
    # Build the graph
    workflow = StateGraph(CategorizationStateDict)
    
    # Add the categorization node
    workflow.add_node("categorize_single_document", categorize_single_document)
    
    # Use conditional edges from start that return Send objects
    workflow.add_conditional_edges("__start__", fan_out_mapper)
    
    # Categorization node connects to the END
    workflow.add_edge("categorize_single_document", END)
    
    return CategorizationWorkflow(workflow)
