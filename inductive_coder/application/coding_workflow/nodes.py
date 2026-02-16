"""Node functions for the Coding workflow."""

from typing import Any

from pydantic import BaseModel, Field

from inductive_coder.domain.entities import Chunk, SentenceCode
from inductive_coder.infrastructure.llm_client import get_llm_client, get_node_model
from inductive_coder.application.coding_workflow.prompts import (
    get_chunking_decision_prompts,
    get_code_chunk_prompts,
)
from inductive_coder.application.coding_workflow.state import CodingStateDict


# Pydantic schemas for structured output

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


# Node functions

async def decide_chunking_node(state: CodingStateDict) -> dict[str, Any]:
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
    
    llm = get_llm_client(model=get_node_model("DECIDE_CHUNKING_MODEL"))
    
    # Create sentence list for the prompt
    sentence_list = "\n".join([f"{s.id}: {s.text}" for s in doc.sentences])
    code_list = "\n".join([f"- {c.name}: {c.description}" for c in code_book.codes])
    
    system_prompt, user_prompt = get_chunking_decision_prompts(
        doc_name=doc.path.name,
        sentence_list=sentence_list,
        code_list=code_list
    )

    response = await llm.generate_structured(
        prompt=user_prompt,
        schema=ChunkingDecisionSchema,
        system_prompt=system_prompt,
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


async def code_chunk_node(state: CodingStateDict) -> dict[str, Any]:
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
    
    llm = get_llm_client(model=get_node_model("CODE_CHUNK_MODEL"))
    
    # Create prompt
    sentence_list = "\n".join([f"{s.id}: {s.text}" for s in chunk.sentences])
    code_list = "\n".join([
        f"- {c.name}: {c.description}\n  Criteria: {c.criteria}"
        for c in code_book.codes
    ])
    
    system_prompt, user_prompt = get_code_chunk_prompts(
        sentence_list=sentence_list,
        code_list=code_list
    )

    response = await llm.generate_structured(
        prompt=user_prompt,
        schema=SentenceCodesSchema,
        system_prompt=system_prompt,
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


async def next_document_node(state: CodingStateDict) -> dict[str, Any]:
    """Move to next document."""
    return {"current_doc_index": state["current_doc_index"] + 1}
