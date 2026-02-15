# Prompts Directory

This directory contains all the prompt templates used in the LangGraph workflow system.

## Files

### `templates.py`
Contains all prompt template functions for the inductive coding workflows.

## Prompt Functions

### Round 1: Reading and Code Book Creation

1. **`get_read_document_prompt()`**
   - **Purpose**: Guide the LLM to read a document and take structured notes
   - **Used in**: `read_document_node` in workflows.py
   - **Inputs**: mode, user_context, doc_name, doc_content
   - **Output**: Notes about themes, patterns, and potential codes

2. **`get_create_codebook_prompt()`**
   - **Purpose**: Generate a comprehensive code book from accumulated notes
   - **Used in**: `create_codebook_node` in workflows.py
   - **Inputs**: mode, user_context, all_notes
   - **Output**: Structured code book with 5-10 codes

### Round 2: Coding Mode

3. **`get_chunking_decision_prompt()`**
   - **Purpose**: Decide whether to chunk a document and define chunk boundaries
   - **Used in**: `decide_chunking_node` in workflows.py
   - **Inputs**: doc_name, sentence_list, code_list
   - **Output**: Chunking decision with chunk ranges and relevance flags

4. **`get_code_chunk_prompt()`**
   - **Purpose**: Apply codes to sentences within a chunk
   - **Used in**: `code_chunk_node` in workflows.py
   - **Inputs**: sentence_list, code_list
   - **Output**: Sentence-code pairs with rationales

### Round 2: Categorization Mode

5. **`get_categorize_document_prompt()`**
   - **Purpose**: Categorize an entire document with appropriate codes
   - **Used in**: `categorize_document_node` in workflows.py
   - **Inputs**: doc_name, doc_content, code_list
   - **Output**: Document-code assignments with rationales

## Usage

Import the appropriate prompt function in your workflow node:

```python
from inductive_coder.application.prompts.templates import get_read_document_prompt

# In your workflow node
prompt = get_read_document_prompt(
    mode=mode.value,
    user_context=user_context,
    doc_name=doc.path.name,
    doc_content=doc.content
)

response = await llm.generate(prompt)
```

## Design Principles

1. **Centralization**: All prompts in one location for easy maintenance
2. **Type Safety**: Function signatures document required parameters
3. **Clarity**: Clear docstrings explain purpose and usage
4. **Consistency**: Similar structure across all prompts
5. **Token Efficiency**: Prompts designed to minimize token usage while maximizing quality

## Modification Guidelines

When modifying prompts:

1. **Test thoroughly**: Changes affect LLM behavior across the entire workflow
2. **Update documentation**: Keep this README in sync with code
3. **Consider token count**: Longer prompts increase API costs
4. **Maintain structure**: Keep the input/output format consistent
5. **Version control**: Document significant changes in commit messages
