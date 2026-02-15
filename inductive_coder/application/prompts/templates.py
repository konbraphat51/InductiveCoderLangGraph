"""Prompt templates for the LangGraph workflows."""


def get_read_document_prompt(mode: str, user_context: str, doc_name: str, doc_content: str) -> str:
    """Get the prompt for reading and taking notes on a document.
    
    Args:
        mode: Analysis mode (coding or categorization)
        user_context: User's research question and context
        doc_name: Name of the document being read
        doc_content: Full content of the document
    
    Returns:
        Formatted prompt string
    """
    return f"""You are analyzing documents for inductive {mode}.

User's research question and context:
{user_context}

Document: {doc_name}
Content:
{doc_content}

Read this document carefully and take notes about:
1. Key themes, patterns, or categories that emerge
2. Important concepts or ideas relevant to the research question
3. Potential codes that could be used to categorize this content

Provide your notes in a clear, structured format."""


def get_create_codebook_prompt(mode: str, user_context: str, all_notes: str) -> str:
    """Get the prompt for creating a code book from accumulated notes.
    
    Args:
        mode: Analysis mode (coding or categorization)
        user_context: User's research question and context
        all_notes: Accumulated notes from reading all documents
    
    Returns:
        Formatted prompt string
    """
    return f"""You are creating a code book for inductive {mode} analysis.

User's research question and context:
{user_context}

Based on your notes from reading all documents:
{all_notes}

Create a comprehensive code book with codes that:
1. Capture the key themes, patterns, and categories in the data
2. Are relevant to the user's research question
3. Have clear criteria for when to apply each code
4. Are mutually exclusive where possible but can overlap when necessary

Provide 5-10 codes that will be most useful for analyzing this data."""


def get_chunking_decision_prompt(doc_name: str, sentence_list: str, code_list: str) -> str:
    """Get the prompt for deciding how to chunk a document.
    
    Args:
        doc_name: Name of the document
        sentence_list: Formatted list of sentences with IDs
        code_list: Formatted list of codes from the code book
    
    Returns:
        Formatted prompt string
    """
    return f"""You are analyzing a document for coding.

Code book:
{code_list}

Document: {doc_name}
Sentences:
{sentence_list}

Decide whether to:
1. Process the entire document at once (if it's short or highly cohesive)
2. Divide it into chunks (if it's long or covers multiple topics)

If chunking, specify:
- The start and end sentence IDs for each chunk
- Whether each chunk is relevant for coding (based on the code book)

This helps minimize LLM token usage by skipping irrelevant sections."""


def get_code_chunk_prompt(sentence_list: str, code_list: str) -> str:
    """Get the prompt for applying codes to a chunk of sentences.
    
    Args:
        sentence_list: Formatted list of sentences with IDs
        code_list: Formatted list of codes with criteria
    
    Returns:
        Formatted prompt string
    """
    return f"""Apply codes to sentences in this chunk.

Code book:
{code_list}

Sentences:
{sentence_list}

For each sentence that matches one or more codes:
1. Identify the sentence ID
2. Apply the appropriate code(s)
3. Provide a brief rationale

Return all sentence-code pairs for this chunk."""


def get_categorize_document_prompt(doc_name: str, doc_content: str, code_list: str) -> str:
    """Get the prompt for categorizing a document.
    
    Args:
        doc_name: Name of the document
        doc_content: Full content of the document
        code_list: Formatted list of codes with criteria
    
    Returns:
        Formatted prompt string
    """
    return f"""Categorize this document using the code book.

Code book:
{code_list}

Document: {doc_name}
Content:
{doc_content}

Apply all relevant codes to this document. You can apply multiple codes if appropriate.
For each code applied, provide a brief rationale."""
