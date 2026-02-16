"""Edge functions for the Categorization workflow."""

from langgraph.graph import END

from inductive_coder.application.categorization_workflow.state import CategorizationStateDict


def should_continue_categorization(state: CategorizationStateDict) -> str:
    """Decide whether to continue categorizing documents."""
    if state["current_doc_index"] < len(state["documents"]):
        return "categorize_document"
    return END
