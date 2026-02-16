"""Use cases for inductive coding analysis."""

from pathlib import Path
from typing import Optional

from inductive_coder.domain.entities import (
    AnalysisMode,
    AnalysisResult,
    CodeBook,
    Document,
    HierarchyDepth,
)
from inductive_coder.domain.repositories import (
    IDocumentRepository,
    ICodeBookRepository,
    IAnalysisResultRepository,
)
from inductive_coder.application.reading_workflow import create_reading_workflow
from inductive_coder.application.coding_workflow import create_coding_workflow
from inductive_coder.application.categorization_workflow import create_categorization_workflow


class CodeBookGenerationUseCase:
    """Use case for generating only a code book (Round 1 only)."""
    
    def __init__(
        self,
        doc_repository: IDocumentRepository,
        code_book_repository: ICodeBookRepository,
    ) -> None:
        self.doc_repo = doc_repository
        self.code_book_repo = code_book_repository
    
    async def execute(
        self,
        mode: AnalysisMode,
        input_dir: Path,
        user_context: str,
        output_path: Path,
        hierarchy_depth: HierarchyDepth = HierarchyDepth.FLAT,
    ) -> CodeBook:
        """
        Execute Round 1 only to generate a code book.
        
        Args:
            mode: Analysis mode (coding or categorization)
            input_dir: Directory containing documents to analyze
            user_context: User's research question and context
            output_path: Path to save the code book
            hierarchy_depth: Hierarchy depth for code structure
        
        Returns:
            Generated CodeBook
        """
        # Load documents
        documents = self.doc_repo.load_documents(input_dir)
        
        if not documents:
            raise ValueError(f"No documents found in {input_dir}")
        
        # Run Round 1
        workflow = create_reading_workflow()
        code_book = await workflow.execute(
            mode=mode,
            documents=documents,
            user_context=user_context,
            hierarchy_depth=hierarchy_depth,
        )
        
        # Save code book
        self.code_book_repo.save_code_book(code_book, output_path)
        
        return code_book


class AnalysisUseCase:
    """Use case for running inductive coding analysis."""
    
    def __init__(
        self,
        doc_repository: IDocumentRepository,
        code_book_repository: ICodeBookRepository,
        result_repository: IAnalysisResultRepository,
    ) -> None:
        self.doc_repo = doc_repository
        self.code_book_repo = code_book_repository
        self.result_repo = result_repository
    
    async def execute(
        self,
        mode: AnalysisMode,
        input_dir: Path,
        user_context: str,
        output_dir: Path,
        existing_code_book: Optional[Path] = None,
        hierarchy_depth: HierarchyDepth = HierarchyDepth.FLAT,
    ) -> AnalysisResult:
        """
        Execute the analysis workflow.
        
        Args:
            mode: Analysis mode (coding or categorization)
            input_dir: Directory containing documents to analyze
            user_context: User's research question and context
            output_dir: Directory to save results
            existing_code_book: Optional path to existing code book (skip round 1)
            hierarchy_depth: Hierarchy depth for code structure
        
        Returns:
            AnalysisResult with codes applied
        """
        # Load documents
        documents = self.doc_repo.load_documents(input_dir)
        
        if not documents:
            raise ValueError(f"No documents found in {input_dir}")
        
        # Round 1 or load existing code book
        if existing_code_book:
            code_book = self.code_book_repo.load_code_book(existing_code_book)
        else:
            reading_workflow = create_reading_workflow()
            code_book = await reading_workflow.execute(
                mode=mode,
                documents=documents,
                user_context=user_context,
                hierarchy_depth=hierarchy_depth,
            )
            
            # Save code book
            code_book_path = output_dir / "code_book.json"
            self.code_book_repo.save_code_book(code_book, code_book_path)
        
        # Round 2
        if mode == AnalysisMode.CODING:
            coding_workflow = create_coding_workflow()
            sentence_codes = await coding_workflow.execute(
                documents=documents,
                code_book=code_book,
            )
            result = AnalysisResult(
                mode=mode,
                code_book=code_book,
                sentence_codes=sentence_codes,
            )
        else:
            categorization_workflow = create_categorization_workflow()
            document_codes = await categorization_workflow.execute(
                documents=documents,
                code_book=code_book,
            )
            result = AnalysisResult(
                mode=mode,
                code_book=code_book,
                document_codes=document_codes,
            )
        
        # Save results
        self.result_repo.save_result(result, output_dir)
        
        return result
