"""Repository implementations for file system storage."""

import json
from pathlib import Path
from typing import Any

from inductive_coder.domain.entities import (
    AnalysisMode,
    AnalysisResult,
    Code,
    CodeBook,
    Document,
    DocumentCode,
    SentenceCode,
)
from inductive_coder.domain.repositories import (
    IAnalysisResultRepository,
    ICodeBookRepository,
    IDocumentRepository,
)


class FileSystemDocumentRepository(IDocumentRepository):
    """File system implementation of document repository."""
    
    def load_document(self, path: Path) -> Document:
        """Load a single document from a file."""
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {path}")
        
        content = path.read_text(encoding="utf-8")
        return Document(path=path, content=content)
    
    def load_documents(self, directory: Path) -> list[Document]:
        """Load all documents from a directory."""
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        documents = []
        
        # Load .txt and .md files
        for pattern in ["*.txt", "*.md"]:
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    doc = self.load_document(file_path)
                    documents.append(doc)
        
        # Sort by name for consistent ordering
        documents.sort(key=lambda d: d.path.name)
        
        return documents
    
    def save_document(self, document: Document, output_path: Path) -> None:
        """Save a document to a file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(document.content, encoding="utf-8")


class JSONCodeBookRepository(ICodeBookRepository):
    """JSON file implementation of code book repository."""
    
    def save_code_book(self, code_book: CodeBook, path: Path) -> None:
        """Save a code book to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "mode": code_book.mode.value,
            "context": code_book.context,
            "codes": [
                {
                    "name": code.name,
                    "description": code.description,
                    "criteria": code.criteria,
                }
                for code in code_book.codes
            ],
        }
        
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_code_book(self, path: Path) -> CodeBook:
        """Load a code book from a JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Code book not found: {path}")
        
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        codes = [
            Code(
                name=c["name"],
                description=c["description"],
                criteria=c["criteria"],
            )
            for c in data["codes"]
        ]
        
        mode = AnalysisMode(data["mode"])
        context = data.get("context", "")
        
        return CodeBook(codes=codes, mode=mode, context=context)


class JSONAnalysisResultRepository(IAnalysisResultRepository):
    """JSON file implementation of analysis result repository."""
    
    def save_result(self, result: AnalysisResult, output_dir: Path) -> None:
        """Save analysis results to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save code book
        code_book_path = output_dir / "code_book.json"
        code_book_repo = JSONCodeBookRepository()
        code_book_repo.save_code_book(result.code_book, code_book_path)
        
        # Save codes
        if result.mode == AnalysisMode.CODING:
            self._save_sentence_codes(result, output_dir)
        else:
            self._save_document_codes(result, output_dir)
        
        # Save summary
        self._save_summary(result, output_dir)
    
    def _save_sentence_codes(self, result: AnalysisResult, output_dir: Path) -> None:
        """Save sentence-level codes."""
        codes_path = output_dir / "sentence_codes.json"
        
        # Group by code
        codes_by_name: dict[str, list[dict[str, Any]]] = {}
        
        for sc in result.sentence_codes:
            if sc.code.name not in codes_by_name:
                codes_by_name[sc.code.name] = []
            
            codes_by_name[sc.code.name].append({
                "sentence_id": sc.sentence_id,
                "rationale": sc.rationale or "",
            })
        
        # Also save by file
        codes_by_file: dict[str, list[dict[str, Any]]] = {}
        
        for sc in result.sentence_codes:
            # Extract file name from sentence ID (format: filename_linenum)
            file_name = "_".join(sc.sentence_id.split("_")[:-1])
            
            if file_name not in codes_by_file:
                codes_by_file[file_name] = []
            
            codes_by_file[file_name].append({
                "sentence_id": sc.sentence_id,
                "code": sc.code.name,
                "rationale": sc.rationale or "",
            })
        
        data = {
            "mode": "coding",
            "total_coded_sentences": len(result.sentence_codes),
            "codes_by_name": codes_by_name,
            "codes_by_file": codes_by_file,
        }
        
        with codes_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_document_codes(self, result: AnalysisResult, output_dir: Path) -> None:
        """Save document-level codes."""
        codes_path = output_dir / "document_codes.json"
        
        # Group by code
        codes_by_name: dict[str, list[dict[str, Any]]] = {}
        
        for dc in result.document_codes:
            if dc.code.name not in codes_by_name:
                codes_by_name[dc.code.name] = []
            
            codes_by_name[dc.code.name].append({
                "file": str(dc.file_path),
                "rationale": dc.rationale or "",
            })
        
        # Also save by file
        codes_by_file: dict[str, list[dict[str, Any]]] = {}
        
        for dc in result.document_codes:
            file_name = dc.file_path.name
            
            if file_name not in codes_by_file:
                codes_by_file[file_name] = []
            
            codes_by_file[file_name].append({
                "code": dc.code.name,
                "rationale": dc.rationale or "",
            })
        
        data = {
            "mode": "categorization",
            "total_coded_documents": len(set(dc.file_path for dc in result.document_codes)),
            "codes_by_name": codes_by_name,
            "codes_by_file": codes_by_file,
        }
        
        with codes_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_summary(self, result: AnalysisResult, output_dir: Path) -> None:
        """Save analysis summary."""
        summary_path = output_dir / "summary.txt"
        
        lines = [
            "=" * 80,
            "INDUCTIVE CODING ANALYSIS SUMMARY",
            "=" * 80,
            "",
            f"Mode: {result.mode.value.upper()}",
            f"Number of codes: {len(result.code_book.codes)}",
            "",
            "CODES:",
        ]
        
        for code in result.code_book.codes:
            lines.append(f"\n{code.name}")
            lines.append(f"  Description: {code.description}")
            lines.append(f"  Criteria: {code.criteria}")
        
        lines.append("\n" + "=" * 80)
        lines.append("RESULTS:")
        lines.append("=" * 80)
        
        if result.mode == AnalysisMode.CODING:
            lines.append(f"\nTotal coded sentences: {len(result.sentence_codes)}")
            
            # Count by code
            code_counts: dict[str, int] = {}
            for sc in result.sentence_codes:
                code_counts[sc.code.name] = code_counts.get(sc.code.name, 0) + 1
            
            lines.append("\nSentences per code:")
            for code_name, count in sorted(code_counts.items()):
                lines.append(f"  {code_name}: {count}")
        else:
            lines.append(f"\nTotal coded documents: {len(set(dc.file_path for dc in result.document_codes))}")
            
            # Count by code
            code_counts: dict[str, int] = {}
            for dc in result.document_codes:
                code_counts[dc.code.name] = code_counts.get(dc.code.name, 0) + 1
            
            lines.append("\nDocuments per code:")
            for code_name, count in sorted(code_counts.items()):
                lines.append(f"  {code_name}: {count}")
        
        lines.append("\n" + "=" * 80)
        
        summary_path.write_text("\n".join(lines), encoding="utf-8")
    
    def load_result(self, output_dir: Path) -> AnalysisResult:
        """Load analysis results from output directory."""
        # Load code book
        code_book_path = output_dir / "code_book.json"
        code_book_repo = JSONCodeBookRepository()
        code_book = code_book_repo.load_code_book(code_book_path)
        
        result = AnalysisResult(mode=code_book.mode, code_book=code_book)
        
        # Load codes based on mode
        if code_book.mode == AnalysisMode.CODING:
            codes_path = output_dir / "sentence_codes.json"
            if codes_path.exists():
                with codes_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Reconstruct sentence codes
                for code_name, sentences in data["codes_by_name"].items():
                    code = code_book.get_code(code_name)
                    if code:
                        for sc_data in sentences:
                            result.add_sentence_code(
                                SentenceCode(
                                    sentence_id=sc_data["sentence_id"],
                                    code=code,
                                    rationale=sc_data.get("rationale"),
                                )
                            )
        else:
            codes_path = output_dir / "document_codes.json"
            if codes_path.exists():
                with codes_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Reconstruct document codes
                for code_name, documents in data["codes_by_name"].items():
                    code = code_book.get_code(code_name)
                    if code:
                        for dc_data in documents:
                            result.add_document_code(
                                DocumentCode(
                                    file_path=Path(dc_data["file"]),
                                    code=code,
                                    rationale=dc_data.get("rationale"),
                                )
                            )
        
        return result
