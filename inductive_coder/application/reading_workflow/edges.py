"""Edge functions for the Reading workflow."""

from inductive_coder.application.reading_workflow.state import ReadingStateDict


def should_continue_reading(state: ReadingStateDict) -> str:
    """Decide whether to continue reading documents."""
    if state["current_doc_index"] < len(state["documents"]):
        return "read_document"
    return "create_codebook"
