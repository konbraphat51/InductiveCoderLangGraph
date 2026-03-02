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
