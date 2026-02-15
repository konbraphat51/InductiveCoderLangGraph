"""Use cases for inductive coding analysis."""

from pathlib import Path
from typing import Optional

from inductive_coder.domain.entities import (
    AnalysisMode,
    AnalysisResult,
    CodeBook,
    Document,
)
from inductive_coder.domain.repositories import (
    IDocumentRepository,
    ICodeBookRepository,
    IAnalysisResultRepository,
)
from inductive_coder.application.workflows import (
    create_round1_workflow,
    create_round2_coding_workflow,
    create_round2_categorization_workflow,
)


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
    ) -> AnalysisResult:
        """
        Execute the analysis workflow.
        
        Args:
            mode: Analysis mode (coding or categorization)
            input_dir: Directory containing documents to analyze
            user_context: User's research question and context
            output_dir: Directory to save results
            existing_code_book: Optional path to existing code book (skip round 1)
        
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
            workflow = create_round1_workflow()
            code_book = await workflow.execute(
                mode=mode,
                documents=documents,
                user_context=user_context,
            )
            
            # Save code book
            code_book_path = output_dir / "code_book.json"
            self.code_book_repo.save_code_book(code_book, code_book_path)
        
        # Round 2
        if mode == AnalysisMode.CODING:
            workflow = create_round2_coding_workflow()
            sentence_codes = await workflow.execute(
                documents=documents,
                code_book=code_book,
            )
            result = AnalysisResult(
                mode=mode,
                code_book=code_book,
                sentence_codes=sentence_codes,
            )
        else:
            workflow = create_round2_categorization_workflow()
            document_codes = await workflow.execute(
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
