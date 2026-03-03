"""Prompt templates for the Reading workflow."""

from typing import Tuple, Optional

from inductive_coder.domain.entities import HierarchyDepth


def get_read_document_prompts(
    mode: str, 
    user_context: str, 
    docs: list[tuple[str, str]],
    current_notes: Optional[str] = None
) -> Tuple[str, str]:
    """Get system and user prompts for reading and taking notes on documents.
    
    Args:
        mode: Analysis mode (coding or categorization)
        user_context: User's research question and context
        docs: List of (doc_name, doc_content) tuples to analyze in one call
        current_notes: Optional current notes (long-term memory) to include in context
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = f"""You are analyzing documents for inductive {mode}.

The user will provide you:
- A research question and context to guide your analysis
- One or more documents to read and analyze\n"""
    
    if current_notes:
        system_prompt += "- Your current notes (long-term memory) from previously analyzed documents\n"
    
    system_prompt += f"""\nYour task is to read documents carefully and take notes about:
1. Key themes, patterns, or categories that emerge
2. Important concepts or ideas relevant to the research question
3. Potential codes that could be used to categorize this content

Provide your notes in a clear, structured format. These notes will serve as your long-term memory for synthesizing a code book later."""
    
    # Add current notes context if exists
    if current_notes:
        system_prompt += f"\n\nThe previous notes will be deleted, and your new notes will be added to long-term memory. So make sure to include every information from previous notes in your new notes."
    
    # Build the documents section
    if len(docs) == 1:
        doc_name, doc_content = docs[0]
        docs_section = f"Document to analyze: {doc_name}\n\nContent:\n{doc_content}"
    else:
        doc_parts = []
        for i, (doc_name, doc_content) in enumerate(docs, 1):
            doc_parts.append(f"### Document {i}: {doc_name}\n\n{doc_content}")
        docs_section = "Documents to analyze:\n\n" + "\n\n---\n\n".join(doc_parts)
    
    user_prompt = f"Research question and context:\n{user_context}"
    if current_notes:
        user_prompt += f"\nYour current notes (long-term memory):\n{current_notes}\n\n"
    user_prompt += f"\n{docs_section}"
    
    return system_prompt, user_prompt



def get_create_codebook_prompts(
    mode: str, 
    user_context: str, 
    all_notes: str,
    hierarchy_depth: HierarchyDepth = HierarchyDepth.FLAT,
) -> Tuple[str, str]:
    """Get system and user prompts for creating a code book from accumulated notes.
    
    Args:
        mode: Analysis mode (coding or categorization)
        user_context: User's research question and context
        all_notes: Accumulated notes from reading all documents
        hierarchy_depth: Hierarchy depth for code structure
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    base_system_prompt = f"""You are creating a code book for inductive {mode}.

Create a comprehensive {mode} book with codes that:
1. Capture the key themes, patterns, and categories in the data
2. Are relevant to the user's research question
3. Have clear criteria for when to apply each code
4. Are mutually exclusive where possible but can overlap when necessary
5. Cover all concepts and ideas, no matter how specific or broad, as long as they are relevant to the research question.
"""
    
    # Add hierarchy instructions based on depth
    if hierarchy_depth == HierarchyDepth.FLAT:
        hierarchy_instruction = f"\n\nCreate a FLAT {mode} structure (no hierarchy). All codes should be at the same level with no parent-child relationships. Do NOT set parent_code_name for any code."
    elif hierarchy_depth == HierarchyDepth.TWO_LEVEL:
        hierarchy_instruction = f"""

Create a TWO-LEVEL hierarchical {mode} structure:
- Maximum depth is 2 levels (parent and child only)
- The top level should be broad categories of the {mode}, and the sub-level should be more specific and meaningful {mode}.
- Parent codes should have parent_code_name = null
"""
    else:  # HierarchyDepth.ARBITRARY
        hierarchy_instruction = """

Create a HIERARCHICAL code structure with ARBITRARY depth:
- You can create multiple levels as needed to best represent the data structure
- Set parent_code_name to organize codes hierarchically
- Top-level codes should have parent_code_name = null
- Sub-codes should have parent_code_name set to their parent's name
- You can nest codes as deeply as necessary to capture the structure of the data"""
    
    system_prompt = base_system_prompt + hierarchy_instruction
    
    user_prompt = f"""Research question and context:
{user_context}

Your notes from reading all documents:
{all_notes}"""
    
    return system_prompt, user_prompt


def get_re_read_document_prompts(
    mode: str,
    user_context: str,
    docs: list[tuple[str, str]],
    code_book_str: str,
    previous_notes: Optional[list[str]] = None,
) -> Tuple[str, str]:
    """Get system and user prompts for re-reading documents with codebook reference.

    Args:
        mode: Analysis mode (coding or categorization)
        user_context: User's research question and context
        docs: List of (doc_name, doc_content) tuples to analyze in one call
        code_book_str: String representation of the existing codebook
        previous_notes: Optional list of missing-code notes from previously processed
            docs/batches in this round (one entry per doc/batch)

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = f"""You are re-analyzing documents for inductive {mode}.

You have already created a codebook based on a first reading. Your task now is to:
1. Read each document again carefully
2. Refer to the existing codebook
3. Note any themes, patterns, or concepts that are NOT yet covered by the existing codes
4. Focus on what is MISSING from the codebook

Your notes should primarily describe gaps and missing codes rather than content already covered."""

    if previous_notes:
        system_prompt += "\n\nNotes from previously analyzed documents in this round are provided below for reference."

    # Build the documents section
    if len(docs) == 1:
        doc_name, doc_content = docs[0]
        docs_section = f"Document to analyze: {doc_name}\n\nContent:\n{doc_content}"
    else:
        doc_parts = []
        for i, (doc_name, doc_content) in enumerate(docs, 1):
            doc_parts.append(f"### Document {i}: {doc_name}\n\n{doc_content}")
        docs_section = "Documents to analyze:\n\n" + "\n\n---\n\n".join(doc_parts)

    user_prompt = f"Research question and context:\n{user_context}\n\n"
    user_prompt += f"Existing codebook:\n{code_book_str}\n\n"
    if previous_notes:
        numbered = "\n\n".join(f"[{i + 1}] {note}" for i, note in enumerate(previous_notes))
        user_prompt += f"Notes on missing codes from previous documents in this round:\n{numbered}\n\n"
    user_prompt += docs_section

    return system_prompt, user_prompt


def get_update_codebook_prompts(
    mode: str,
    user_context: str,
    missing_codes_notes: str,
    existing_codebook_str: str,
    hierarchy_depth: HierarchyDepth = HierarchyDepth.FLAT,
) -> Tuple[str, str]:
    """Get system and user prompts for updating the codebook with missing codes.

    Args:
        mode: Analysis mode (coding or categorization)
        user_context: User's research question and context
        missing_codes_notes: Notes describing codes missing from the current codebook
        existing_codebook_str: String representation of the existing codebook
        hierarchy_depth: Hierarchy depth for code structure

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    base_system_prompt = f"""You are expanding a code book for inductive {mode}.

You have an existing codebook and notes describing codes that appear to be missing.
Your task is to return a complete, updated codebook that:
1. Retains ALL existing codes unchanged
2. Adds new codes identified from the missing-codes notes
3. Ensures new codes are relevant to the research question
4. Ensures new codes have clear criteria and do not duplicate existing codes
"""

    # Add hierarchy instructions based on depth
    if hierarchy_depth == HierarchyDepth.FLAT:
        hierarchy_instruction = f"\n\nMaintain a FLAT {mode} structure (no hierarchy). All codes should be at the same level with no parent-child relationships. Do NOT set parent_code_name for any code."
    elif hierarchy_depth == HierarchyDepth.TWO_LEVEL:
        hierarchy_instruction = f"""

Maintain the TWO-LEVEL hierarchical {mode} structure:
- Maximum depth is 2 levels (parent and child only)
- The top level should be broad categories, and the sub-level should be more specific codes.
- Parent codes should have parent_code_name = null
"""
    else:  # HierarchyDepth.ARBITRARY
        hierarchy_instruction = """

Maintain the HIERARCHICAL code structure with ARBITRARY depth:
- You can create multiple levels as needed
- Set parent_code_name to organize codes hierarchically
- Top-level codes should have parent_code_name = null"""

    system_prompt = base_system_prompt + hierarchy_instruction

    user_prompt = f"""Research question and context:
{user_context}

Existing codebook:
{existing_codebook_str}

Notes on missing codes from re-reading:
{missing_codes_notes}"""

    return system_prompt, user_prompt
