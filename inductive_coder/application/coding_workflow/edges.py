"""Edge functions for the Coding workflow."""

from langgraph.graph import END

from inductive_coder.application.coding_workflow.state import CodingStateDict


def should_continue_coding_chunks(state: CodingStateDict) -> str:
    """Decide whether to continue coding chunks."""
    if state["current_chunk_index"] < len(state["chunks"]):
        return "code_chunk"
    return "next_document"


def should_continue_coding_documents(state: CodingStateDict) -> str:
    """Decide whether to continue with next document."""
    if state["current_doc_index"] < len(state["documents"]) - 1:
        return "decide_chunking"
    return END
