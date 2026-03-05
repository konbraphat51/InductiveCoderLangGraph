"""Edge functions for the Reading workflow."""

from inductive_coder.application.reading_workflow.state import ReadingStateDict


def should_continue_reading(state: ReadingStateDict) -> str:
    """Decide whether to continue reading documents."""
    if state["current_doc_index"] < len(state["documents"]):
        return "read_document"
    return "create_codebook"


def should_start_re_reading(state: ReadingStateDict) -> str:
    """Decide whether to start re-reading rounds after the initial codebook is created."""
    re_reading_rounds = state.get("re_reading_rounds", 0)
    current_round = state.get("current_round", 1)
    if re_reading_rounds > 0 and current_round <= re_reading_rounds:
        return "re_read_document"
    return "__end__"


def should_continue_re_reading(state: ReadingStateDict) -> str:
    """Decide whether to continue re-reading documents in the current round."""
    if state["current_doc_index"] < len(state["documents"]):
        return "re_read_document"
    return "update_codebook"


def should_continue_rounds(state: ReadingStateDict) -> str:
    """Decide whether to start another re-reading round after updating the codebook."""
    re_reading_rounds = state.get("re_reading_rounds", 0)
    current_round = state.get("current_round", 1)
    if current_round <= re_reading_rounds:
        return "re_read_document"
    return "__end__"
