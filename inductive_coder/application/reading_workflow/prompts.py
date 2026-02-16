"""Prompt templates for the Reading workflow."""

from typing import Tuple


def get_read_document_prompts(mode: str, user_context: str, doc_name: str, doc_content: str) -> Tuple[str, str]:
    """Get system and user prompts for reading and taking notes on a document.
    
    Args:
        mode: Analysis mode (coding or categorization)
        user_context: User's research question and context
        doc_name: Name of the document being read
        doc_content: Full content of the document
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = f"""You are analyzing documents for inductive {mode}.

Your task is to read documents carefully and take notes about:
1. Key themes, patterns, or categories that emerge
2. Important concepts or ideas relevant to the research question
3. Potential codes that could be used to categorize this content

Provide your notes in a clear, structured format. These notes will serve as your long-term memory for synthesizing a code book later."""
    
    user_prompt = f"""Research question and context:
{user_context}

Document to analyze: {doc_name}

Content:
{doc_content}"""
    
    return system_prompt, user_prompt


def get_create_codebook_prompts(mode: str, user_context: str, all_notes: str) -> Tuple[str, str]:
    """Get system and user prompts for creating a code book from accumulated notes.
    
    Args:
        mode: Analysis mode (coding or categorization)
        user_context: User's research question and context
        all_notes: Accumulated notes from reading all documents
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = f"""You are creating a code book for inductive {mode} analysis.

Create a comprehensive code book with codes that:
1. Capture the key themes, patterns, and categories in the data
2. Are relevant to the user's research question
3. Have clear criteria for when to apply each code
4. Are mutually exclusive where possible but can overlap when necessary

Provide 5-10 codes that will be most useful for analyzing this data."""
    
    user_prompt = f"""Research question and context:
{user_context}

Your notes from reading all documents:
{all_notes}"""
    
    return system_prompt, user_prompt
