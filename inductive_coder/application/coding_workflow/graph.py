"""Graph construction for the Coding workflow."""

from typing import Any, Optional, Callable

from langgraph.graph import StateGraph, END

from inductive_coder.domain.entities import CodeBook, Document, SentenceCode
from inductive_coder.application.coding_workflow.state import (
    CodingStateDict,
    SingleDocCodingState,
)
from inductive_coder.application.coding_workflow.nodes import (
    fan_out_documents,
    decide_chunking_node,
    code_chunk_node,
)
from inductive_coder.application.coding_workflow.edges import (
    should_continue_coding_chunks,
)


class CodingWorkflow:
    """Wrapper for Coding workflow."""
    
    def __init__(self, graph: StateGraph) -> None:
        self.app = graph.compile()
    
    async def execute(
        self,
        documents: list[Document],
        code_book: CodeBook,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> list[SentenceCode]:
        """Execute Coding workflow."""
        initial_state: CodingStateDict = {
            "documents": documents,
            "code_book": code_book,
            "sentence_codes": [],
            "processed_documents": 0,
            "progress_callback": progress_callback,
        }
        
        result = await self.app.ainvoke(initial_state)
        return result["sentence_codes"]


def create_coding_workflow() -> CodingWorkflow:
    """Create the Coding workflow graph."""
    
    # Build the graph
    workflow = StateGraph(CodingStateDict)
    
    # Add nodes
    workflow.add_node("fan_out", fan_out_documents)
    workflow.add_node("decide_chunking", decide_chunking_node)
    workflow.add_node("code_chunk", code_chunk_node)
    
    # Set entry point
    workflow.set_entry_point("fan_out")
    
    # Add edges - fan_out sends to decide_chunking in parallel for each document
    workflow.add_conditional_edges("fan_out", lambda x: x)
    
    # Within each document, process chunks sequentially
    workflow.add_conditional_edges(
        "code_chunk",
        should_continue_coding_chunks,
        {
            "code_chunk": "code_chunk",
            END: END,
        }
    )
    
    workflow.add_edge("decide_chunking", "code_chunk")
    
    return CodingWorkflow(workflow)
