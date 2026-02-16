"""Graph construction for the Categorization workflow."""

from typing import Any

from langgraph.graph import StateGraph, END

from inductive_coder.domain.entities import CodeBook, Document, DocumentCode
from inductive_coder.application.categorization_workflow.state import CategorizationStateDict
from inductive_coder.application.categorization_workflow.nodes import categorize_document_node
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
        """Execute Categorization workflow."""
        initial_state: CategorizationStateDict = {
            "documents": documents,
            "code_book": code_book,
            "current_doc_index": 0,
            "document_codes": [],
        }
        
        result = await self.app.ainvoke(initial_state)
        return result["document_codes"]


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
