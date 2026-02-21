"""Prompt templates for the Categorization workflow."""

from typing import Tuple


def get_categorize_document_prompts(doc_name: str, doc_content: str, code_list: str, user_context: str) -> Tuple[str, str]:
    """Get system and user prompts for categorizing a document.
    
    Args:
        doc_name: Name of the document
        doc_content: Full content of the document
        code_list: Formatted list of codes with criteria
        user_context: User's research question and context
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = """Categorize this document using the code book.

Apply all relevant codes to this document. You can apply multiple codes if appropriate.
For each code applied, provide a brief rationale."""
    
    user_prompt = f"""Research Context:
{user_context}

Code book:
{code_list}

Document: {doc_name}

Content:
{doc_content}"""
    
    return system_prompt, user_prompt
