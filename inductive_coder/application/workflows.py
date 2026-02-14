"""LangGraph workflows for inductive coding."""

from typing import Any, Callable, TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from inductive_coder.domain.entities import (
    AnalysisMode,
    Code,
    CodeBook,
    Chunk,
    Document,
    SentenceCode,
    DocumentCode,
)
from inductive_coder.infrastructure.llm_client import get_llm_client


# Pydantic schemas for structured output

class CodeSchema(BaseModel):
    """Schema for a single code."""
    name: str = Field(description="Short, descriptive name for the code")
    description: str = Field(description="What this code represents")
    criteria: str = Field(description="When to apply this code")


class CodeBookSchema(BaseModel):
    """Schema for the code book."""
    codes: list[CodeSchema] = Field(description="List of codes to use for analysis")


class ChunkRangeSchema(BaseModel):
    """Schema for a chunk range."""
    start_sentence_id: str = Field(description="ID of the first sentence in the chunk")
    end_sentence_id: str = Field(description="ID of the last sentence in the chunk")
    should_code: bool = Field(description="Whether this chunk is relevant for coding")


class ChunkingDecisionSchema(BaseModel):
    """Schema for chunking decision."""
    should_chunk: bool = Field(description="Whether to divide the document into chunks")
    chunks: list[ChunkRangeSchema] = Field(
        default_factory=list,
        description="List of chunk ranges if should_chunk is True"
    )


class SentenceCodeSchema(BaseModel):
    """Schema for a sentence code."""
    sentence_id: str = Field(description="ID of the sentence")
    code_name: str = Field(description="Name of the code to apply")
    rationale: str = Field(default="", description="Why this code was applied")


class SentenceCodesSchema(BaseModel):
    """Schema for multiple sentence codes."""
    codes: list[SentenceCodeSchema] = Field(description="List of sentence codes")


class DocumentCodeSchema(BaseModel):
    """Schema for document codes."""
    code_names: list[str] = Field(description="Names of codes to apply to this document")
    rationales: dict[str, str] = Field(
        default_factory=dict,
        description="Rationale for each code (code_name -> rationale)"
    )


# TypedDict for LangGraph state

class Round1StateDict(TypedDict):
    """State dict for Round 1."""
    mode: AnalysisMode
    documents: list[Document]
    user_context: str
    notes: Annotated[list[str], operator.add]
    current_doc_index: int
    code_book: CodeBook | None


class Round2CodingStateDict(TypedDict):
    """State dict for Round 2 coding."""
    documents: list[Document]
    code_book: CodeBook
    current_doc_index: int
    current_doc: Document | None
    chunks: list[Chunk]
    current_chunk_index: int
    sentence_codes: Annotated[list[SentenceCode], operator.add]


class Round2CategorizationStateDict(TypedDict):
    """State dict for Round 2 categorization."""
    documents: list[Document]
    code_book: CodeBook
    current_doc_index: int
    document_codes: Annotated[list[DocumentCode], operator.add]


# Round 1: Reading and code book creation

async def read_document_node(state: Round1StateDict) -> dict[str, Any]:
    """Read a document and take notes."""
    current_idx = state["current_doc_index"]
    documents = state["documents"]
    
    if current_idx >= len(documents):
        return {"current_doc_index": current_idx}
    
    doc = documents[current_idx]
    user_context = state["user_context"]
    mode = state["mode"]
    
    llm = get_llm_client()
    
    # Create prompt for reading and note-taking
    prompt = f"""You are analyzing documents for inductive {mode.value}.

User's research question and context:
{user_context}

Document: {doc.path.name}
Content:
{doc.content}

Read this document carefully and take notes about:
1. Key themes, patterns, or categories that emerge
2. Important concepts or ideas relevant to the research question
3. Potential codes that could be used to categorize this content

Provide your notes in a clear, structured format."""

    response = await llm.generate(prompt)
    
    return {
        "notes": [f"Document {doc.path.name}:\n{response}"],
        "current_doc_index": current_idx + 1,
    }


def should_continue_reading(state: Round1StateDict) -> str:
    """Decide whether to continue reading documents."""
    if state["current_doc_index"] < len(state["documents"]):
        return "read_document"
    return "create_codebook"


async def create_codebook_node(state: Round1StateDict) -> dict[str, Any]:
    """Create code book from accumulated notes."""
    notes = state["notes"]
    user_context = state["user_context"]
    mode = state["mode"]
    
    llm = get_llm_client()
    
    # Create prompt for code book generation
    all_notes = "\n\n".join(notes)
    
    prompt = f"""You are creating a code book for inductive {mode.value} analysis.

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

    response = await llm.generate_structured(
        prompt=prompt,
        schema=CodeBookSchema,
    )
    
    # Convert to domain entities
    codes = [
        Code(name=c["name"], description=c["description"], criteria=c["criteria"])
        for c in response["codes"]
    ]
    
    code_book = CodeBook(codes=codes, mode=mode, context=user_context)
    
    return {"code_book": code_book}


def create_round1_workflow() -> Any:
    """Create the Round 1 workflow graph."""
    
    class Round1Workflow:
        """Wrapper for Round 1 workflow."""
        
        def __init__(self, graph: StateGraph) -> None:
            self.app = graph.compile()
        
        async def execute(
            self,
            mode: AnalysisMode,
            documents: list[Document],
            user_context: str,
        ) -> CodeBook:
            """Execute Round 1 workflow."""
            initial_state: Round1StateDict = {
                "mode": mode,
                "documents": documents,
                "user_context": user_context,
                "notes": [],
                "current_doc_index": 0,
                "code_book": None,
            }
            
            result = await self.app.ainvoke(initial_state)
            return result["code_book"]
    
    # Build the graph
    workflow = StateGraph(Round1StateDict)
    
    workflow.add_node("read_document", read_document_node)
    workflow.add_node("create_codebook", create_codebook_node)
    
    workflow.set_entry_point("read_document")
    
    workflow.add_conditional_edges(
        "read_document",
        should_continue_reading,
        {
            "read_document": "read_document",
            "create_codebook": "create_codebook",
        }
    )
    
    workflow.add_edge("create_codebook", END)
    
    return Round1Workflow(workflow)


# Round 2: Coding mode

async def decide_chunking_node(state: Round2CodingStateDict) -> dict[str, Any]:
    """Decide how to chunk the current document."""
    current_idx = state["current_doc_index"]
    documents = state["documents"]
    
    if current_idx >= len(documents):
        return {
            "current_doc": None,
            "chunks": [],
            "current_chunk_index": 0,
        }
    
    doc = documents[current_idx]
    code_book = state["code_book"]
    
    llm = get_llm_client()
    
    # Create sentence list for the prompt
    sentence_list = "\n".join([f"{s.id}: {s.text}" for s in doc.sentences])
    code_list = "\n".join([f"- {c.name}: {c.description}" for c in code_book.codes])
    
    prompt = f"""You are analyzing a document for coding.

Code book:
{code_list}

Document: {doc.path.name}
Sentences:
{sentence_list}

Decide whether to:
1. Process the entire document at once (if it's short or highly cohesive)
2. Divide it into chunks (if it's long or covers multiple topics)

If chunking, specify:
- The start and end sentence IDs for each chunk
- Whether each chunk is relevant for coding (based on the code book)

This helps minimize LLM token usage by skipping irrelevant sections."""

    response = await llm.generate_structured(
        prompt=prompt,
        schema=ChunkingDecisionSchema,
    )
    
    # Create chunks
    chunks: list[Chunk] = []
    
    if not response["should_chunk"]:
        # Single chunk with all sentences
        if doc.sentences:
            chunks = [
                Chunk(
                    start_sentence_id=doc.sentences[0].id,
                    end_sentence_id=doc.sentences[-1].id,
                    sentences=doc.sentences,
                    should_code=True,
                )
            ]
    else:
        # Multiple chunks
        for chunk_range in response["chunks"]:
            # Find sentences in range
            start_id = chunk_range["start_sentence_id"]
            end_id = chunk_range["end_sentence_id"]
            
            chunk_sentences = []
            in_range = False
            
            for sentence in doc.sentences:
                if sentence.id == start_id:
                    in_range = True
                if in_range:
                    chunk_sentences.append(sentence)
                if sentence.id == end_id:
                    break
            
            if chunk_sentences:
                chunks.append(
                    Chunk(
                        start_sentence_id=start_id,
                        end_sentence_id=end_id,
                        sentences=chunk_sentences,
                        should_code=chunk_range["should_code"],
                    )
                )
    
    return {
        "current_doc": doc,
        "chunks": chunks,
        "current_chunk_index": 0,
    }


async def code_chunk_node(state: Round2CodingStateDict) -> dict[str, Any]:
    """Apply codes to a chunk of sentences."""
    chunks = state["chunks"]
    current_chunk_idx = state["current_chunk_index"]
    code_book = state["code_book"]
    
    if current_chunk_idx >= len(chunks):
        return {"current_chunk_index": current_chunk_idx}
    
    chunk = chunks[current_chunk_idx]
    
    # Skip if not relevant
    if not chunk.should_code:
        return {"current_chunk_index": current_chunk_idx + 1}
    
    llm = get_llm_client()
    
    # Create prompt
    sentence_list = "\n".join([f"{s.id}: {s.text}" for s in chunk.sentences])
    code_list = "\n".join([
        f"- {c.name}: {c.description}\n  Criteria: {c.criteria}"
        for c in code_book.codes
    ])
    
    prompt = f"""Apply codes to sentences in this chunk.

Code book:
{code_list}

Sentences:
{sentence_list}

For each sentence that matches one or more codes:
1. Identify the sentence ID
2. Apply the appropriate code(s)
3. Provide a brief rationale

Return all sentence-code pairs for this chunk."""

    response = await llm.generate_structured(
        prompt=prompt,
        schema=SentenceCodesSchema,
    )
    
    # Convert to domain entities
    sentence_codes: list[SentenceCode] = []
    
    for sc in response["codes"]:
        code = code_book.get_code(sc["code_name"])
        if code:
            sentence_codes.append(
                SentenceCode(
                    sentence_id=sc["sentence_id"],
                    code=code,
                    rationale=sc.get("rationale"),
                )
            )
    
    return {
        "sentence_codes": sentence_codes,
        "current_chunk_index": current_chunk_idx + 1,
    }


def should_continue_coding_chunks(state: Round2CodingStateDict) -> str:
    """Decide whether to continue coding chunks."""
    if state["current_chunk_index"] < len(state["chunks"]):
        return "code_chunk"
    return "next_document"


def should_continue_coding_documents(state: Round2CodingStateDict) -> str:
    """Decide whether to continue with next document."""
    if state["current_doc_index"] < len(state["documents"]) - 1:
        return "decide_chunking"
    return END


async def next_document_node(state: Round2CodingStateDict) -> dict[str, Any]:
    """Move to next document."""
    return {"current_doc_index": state["current_doc_index"] + 1}


def create_round2_coding_workflow() -> Any:
    """Create the Round 2 coding workflow graph."""
    
    class Round2CodingWorkflow:
        """Wrapper for Round 2 coding workflow."""
        
        def __init__(self, graph: StateGraph) -> None:
            self.app = graph.compile()
        
        async def execute(
            self,
            documents: list[Document],
            code_book: CodeBook,
        ) -> list[SentenceCode]:
            """Execute Round 2 coding workflow."""
            initial_state: Round2CodingStateDict = {
                "documents": documents,
                "code_book": code_book,
                "current_doc_index": 0,
                "current_doc": None,
                "chunks": [],
                "current_chunk_index": 0,
                "sentence_codes": [],
            }
            
            result = await self.app.ainvoke(initial_state)
            return result["sentence_codes"]
    
    # Build the graph
    workflow = StateGraph(Round2CodingStateDict)
    
    workflow.add_node("decide_chunking", decide_chunking_node)
    workflow.add_node("code_chunk", code_chunk_node)
    workflow.add_node("next_document", next_document_node)
    
    workflow.set_entry_point("decide_chunking")
    
    workflow.add_conditional_edges(
        "code_chunk",
        should_continue_coding_chunks,
        {
            "code_chunk": "code_chunk",
            "next_document": "next_document",
        }
    )
    
    workflow.add_conditional_edges(
        "next_document",
        should_continue_coding_documents,
        {
            "decide_chunking": "decide_chunking",
            END: END,
        }
    )
    
    workflow.add_edge("decide_chunking", "code_chunk")
    
    return Round2CodingWorkflow(workflow)


# Round 2: Categorization mode

async def categorize_document_node(state: Round2CategorizationStateDict) -> dict[str, Any]:
    """Categorize a single document."""
    current_idx = state["current_doc_index"]
    documents = state["documents"]
    
    if current_idx >= len(documents):
        return {"current_doc_index": current_idx}
    
    doc = documents[current_idx]
    code_book = state["code_book"]
    
    llm = get_llm_client()
    
    # Create prompt
    code_list = "\n".join([
        f"- {c.name}: {c.description}\n  Criteria: {c.criteria}"
        for c in code_book.codes
    ])
    
    prompt = f"""Categorize this document using the code book.

Code book:
{code_list}

Document: {doc.path.name}
Content:
{doc.content}

Apply all relevant codes to this document. You can apply multiple codes if appropriate.
For each code applied, provide a brief rationale."""

    response = await llm.generate_structured(
        prompt=prompt,
        schema=DocumentCodeSchema,
    )
    
    # Convert to domain entities
    document_codes: list[DocumentCode] = []
    
    for code_name in response["code_names"]:
        code = code_book.get_code(code_name)
        if code:
            rationale = response.get("rationales", {}).get(code_name)
            document_codes.append(
                DocumentCode(
                    file_path=doc.path,
                    code=code,
                    rationale=rationale,
                )
            )
    
    return {
        "document_codes": document_codes,
        "current_doc_index": current_idx + 1,
    }


def should_continue_categorization(state: Round2CategorizationStateDict) -> str:
    """Decide whether to continue categorizing documents."""
    if state["current_doc_index"] < len(state["documents"]):
        return "categorize_document"
    return END


def create_round2_categorization_workflow() -> Any:
    """Create the Round 2 categorization workflow graph."""
    
    class Round2CategorizationWorkflow:
        """Wrapper for Round 2 categorization workflow."""
        
        def __init__(self, graph: StateGraph) -> None:
            self.app = graph.compile()
        
        async def execute(
            self,
            documents: list[Document],
            code_book: CodeBook,
        ) -> list[DocumentCode]:
            """Execute Round 2 categorization workflow."""
            initial_state: Round2CategorizationStateDict = {
                "documents": documents,
                "code_book": code_book,
                "current_doc_index": 0,
                "document_codes": [],
            }
            
            result = await self.app.ainvoke(initial_state)
            return result["document_codes"]
    
    # Build the graph
    workflow = StateGraph(Round2CategorizationStateDict)
    
    workflow.add_node("categorize_document", categorize_document_node)
    
    workflow.set_entry_point("categorize_document")
    
    workflow.add_conditional_edges(
        "categorize_document",
        should_continue_categorization,
        {
            "categorize_document": "categorize_document",
            END: END,
        }
    )
    
    return Round2CategorizationWorkflow(workflow)
