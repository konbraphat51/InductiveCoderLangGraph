"""Prompt templates for the Coding workflow."""

from typing import Tuple


def get_chunking_decision_prompts(doc_name: str, sentence_list: str, code_list: str) -> Tuple[str, str]:
    """Get system and user prompts for deciding how to chunk a document.
    
    Args:
        doc_name: Name of the document
        sentence_list: Formatted list of sentences with IDs
        code_list: Formatted list of codes from the code book
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = """You are analyzing a document for coding.

Decide whether to:
1. Process the entire document at once (if it's short or highly cohesive)
2. Divide it into chunks (if it's long or covers multiple topics)

If chunking, specify:
- The start and end sentence IDs for each chunk
- Whether each chunk is relevant for coding (based on the code book)

This helps minimize LLM token usage by skipping irrelevant sections."""
    
    user_prompt = f"""Code book:
{code_list}

Document: {doc_name}

Sentences:
{sentence_list}"""
    
    return system_prompt, user_prompt


def get_code_chunk_prompts(sentence_list: str, code_list: str) -> Tuple[str, str]:
    """Get system and user prompts for applying codes to a chunk of sentences.
    
    Args:
        sentence_list: Formatted list of sentences with IDs
        code_list: Formatted list of codes with criteria
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = """Apply codes to sentences in this chunk.

For each sentence that matches one or more codes:
1. Identify the sentence ID
2. Apply the appropriate code(s)
3. Provide a brief rationale

Return all sentence-code pairs for this chunk."""
    
    user_prompt = f"""Code book:
{code_list}

Sentences to code:
{sentence_list}"""
    
    return system_prompt, user_prompt
