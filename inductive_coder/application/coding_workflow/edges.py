"""Edge functions for the Coding workflow."""

from langgraph.graph import END

from inductive_coder.application.coding_workflow.state import SingleDocCodingState


def should_continue_coding_chunks(state: SingleDocCodingState) -> str:
    """Decide whether to continue coding chunks."""
    if state["current_chunk_index"] < len(state["chunks"]):
        return "code_chunk"
    return END
