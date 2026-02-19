"""Use cases for inductive coding analysis."""

from pathlib import Path
from typing import Optional, Callable

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
from inductive_coder.logger import logger


# Type for progress callback: (workflow_name, current, total)
ProgressCallback = Callable[[str, int, int], None]


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
        progress_callback: Optional[ProgressCallback] = None,
    ) -> CodeBook:
        """
        Execute Round 1 only to generate a code book.
        
        Args:
            mode: Analysis mode (coding or categorization)
            input_dir: Directory containing documents to analyze
            user_context: User's research question and context
            output_path: Path to save the code book
            hierarchy_depth: Hierarchy depth for code structure
            progress_callback: Optional callback to report progress (workflow_name, current, total)
        
        Returns:
            Generated CodeBook
        """
        # Load documents
        documents = self.doc_repo.load_documents(input_dir)
        
        if not documents:
            raise ValueError(f"No documents found in {input_dir}")
        
        total_docs = len(documents)
        logger.info("=== CodeBook Generation: %d documents, mode=%s ===", total_docs, mode.value)
        
        # Run Round 1 (Reading workflow)
        logger.info("--- Reading workflow start ---")
        if progress_callback:
            progress_callback("Reading", 0, total_docs)
        
        workflow = create_reading_workflow()
        code_book = await workflow.execute(
            mode=mode,
            documents=documents,
            user_context=user_context,
            hierarchy_depth=hierarchy_depth,
            progress_callback=progress_callback,
        )
        
        if progress_callback:
            progress_callback("Reading", total_docs, total_docs)
        
        logger.info("--- Reading workflow complete ---")
        
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
        progress_callback: Optional[ProgressCallback] = None,
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
            progress_callback: Optional callback to report progress (workflow_name, current, total)
        
        Returns:
            AnalysisResult with codes applied
        """
        # Load documents
        documents = self.doc_repo.load_documents(input_dir)
        
        if not documents:
            raise ValueError(f"No documents found in {input_dir}")
        
        total_docs = len(documents)
        logger.info("=== Analysis: %d documents, mode=%s ===", total_docs, mode.value)
        
        # Round 1 or load existing code book
        if existing_code_book:
            logger.info("Loading existing code book: %s", existing_code_book)
            code_book = self.code_book_repo.load_code_book(existing_code_book)
        else:
            logger.info("--- Reading workflow start ---")
            if progress_callback:
                progress_callback("Reading", 0, total_docs)
            
            reading_workflow = create_reading_workflow()
            code_book = await reading_workflow.execute(
                mode=mode,
                documents=documents,
                user_context=user_context,
                hierarchy_depth=hierarchy_depth,
                progress_callback=progress_callback,
            )
            
            if progress_callback:
                progress_callback("Reading", total_docs, total_docs)
            
            logger.info("--- Reading workflow complete ---")
            
            # Save code book
            code_book_path = output_dir / "code_book.json"
            self.code_book_repo.save_code_book(code_book, code_book_path)
        
        # Round 2
        if mode == AnalysisMode.CODING:
            logger.info("--- Coding workflow start ---")
            if progress_callback:
                progress_callback("Coding", 0, total_docs)
            
            coding_workflow = create_coding_workflow()
            sentence_codes = await coding_workflow.execute(
                documents=documents,
                code_book=code_book,
                progress_callback=progress_callback,
            )
            
            if progress_callback:
                progress_callback("Coding", total_docs, total_docs)
            
            logger.info("--- Coding workflow complete ---")
            
            result = AnalysisResult(
                mode=mode,
                code_book=code_book,
                sentence_codes=sentence_codes,
            )
        else:
            logger.info("--- Categorization workflow start ---")
            if progress_callback:
                progress_callback("Categorization", 0, total_docs)
            
            categorization_workflow = create_categorization_workflow()
            document_codes = await categorization_workflow.execute(
                documents=documents,
                code_book=code_book,
                progress_callback=progress_callback,
            )
            
            if progress_callback:
                progress_callback("Categorization", total_docs, total_docs)
            
            logger.info("--- Categorization workflow complete ---")
            
            result = AnalysisResult(
                mode=mode,
                code_book=code_book,
                document_codes=document_codes,
            )
        
        # Save results
        self.result_repo.save_result(result, output_dir)
        logger.info("=== Analysis complete. Results saved to: %s ===", output_dir)
        
        return result
