"""Interactive UI for viewing analysis results."""

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.prompt import Prompt
from rich.text import Text

from inductive_coder.domain.entities import AnalysisMode
from inductive_coder.infrastructure.repositories import JSONAnalysisResultRepository


def launch_ui(results_dir: Path) -> None:
    """Launch the interactive UI."""
    console = Console()
    
    # Load results
    repo = JSONAnalysisResultRepository()
    result = repo.load_result(results_dir)
    
    console.clear()
    console.print(Panel.fit(
        f"[bold cyan]Inductive Coding Results Viewer[/bold cyan]\n"
        f"Mode: {result.mode.value.upper()}",
        border_style="cyan"
    ))
    
    if result.mode == AnalysisMode.CODING:
        show_coding_ui(console, result, results_dir)
    else:
        show_categorization_ui(console, result, results_dir)


def show_coding_ui(console: Console, result: Any, results_dir: Path) -> None:
    """Show UI for coding mode results."""
    
    while True:
        console.print("\n[bold]Options:[/bold]")
        console.print("1. View codes by file")
        console.print("2. View sentences by code")
        console.print("3. Show code book")
        console.print("4. Show summary statistics")
        console.print("5. Exit")
        
        choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5"], default="5")
        
        if choice == "1":
            view_codes_by_file(console, result, results_dir)
        elif choice == "2":
            view_sentences_by_code(console, result, results_dir)
        elif choice == "3":
            show_code_book(console, result)
        elif choice == "4":
            show_statistics(console, result)
        elif choice == "5":
            break
        
        console.print()


def show_categorization_ui(console: Console, result: Any, results_dir: Path) -> None:
    """Show UI for categorization mode results."""
    
    while True:
        console.print("\n[bold]Options:[/bold]")
        console.print("1. View codes by document")
        console.print("2. View documents by code")
        console.print("3. Show code book")
        console.print("4. Show summary statistics")
        console.print("5. Exit")
        
        choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5"], default="5")
        
        if choice == "1":
            view_doc_codes_by_file(console, result)
        elif choice == "2":
            view_documents_by_code(console, result)
        elif choice == "3":
            show_code_book(console, result)
        elif choice == "4":
            show_statistics(console, result)
        elif choice == "5":
            break
        
        console.print()


def view_codes_by_file(console: Console, result: Any, results_dir: Path) -> None:
    """View sentence codes grouped by file."""
    
    # Load the JSON for file grouping
    codes_path = results_dir / "sentence_codes.json"
    with codes_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    console.print("\n[bold cyan]Codes by File[/bold cyan]\n")
    
    for file_name, codes in sorted(data["codes_by_file"].items()):
        console.print(f"[bold yellow]{file_name}[/bold yellow]")
        
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Sentence ID", style="dim")
        table.add_column("Code", style="cyan")
        table.add_column("Rationale")
        
        for code_info in codes:
            table.add_row(
                code_info["sentence_id"],
                code_info["code"],
                code_info.get("rationale", "")
            )
        
        console.print(table)
        console.print()


def view_sentences_by_code(console: Console, result: Any, results_dir: Path) -> None:
    """View sentences grouped by code."""
    
    # Load the JSON for code grouping
    codes_path = results_dir / "sentence_codes.json"
    with codes_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    console.print("\n[bold cyan]Sentences by Code[/bold cyan]\n")
    
    for code_name, sentences in sorted(data["codes_by_name"].items()):
        console.print(f"[bold green]{code_name}[/bold green] ({len(sentences)} sentences)")
        
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Sentence ID", style="dim")
        table.add_column("Rationale")
        
        for sent_info in sentences:
            table.add_row(
                sent_info["sentence_id"],
                sent_info.get("rationale", "")
            )
        
        console.print(table)
        console.print()


def view_doc_codes_by_file(console: Console, result: Any) -> None:
    """View document codes grouped by file."""
    
    console.print("\n[bold cyan]Codes by Document[/bold cyan]\n")
    
    # Group by file
    codes_by_file: dict[str, list[Any]] = {}
    for dc in result.document_codes:
        file_name = dc.file_path.name
        if file_name not in codes_by_file:
            codes_by_file[file_name] = []
        codes_by_file[file_name].append(dc)
    
    for file_name, doc_codes in sorted(codes_by_file.items()):
        console.print(f"[bold yellow]{file_name}[/bold yellow]")
        
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Code", style="cyan")
        table.add_column("Rationale")
        
        for dc in doc_codes:
            table.add_row(dc.code.name, dc.rationale or "")
        
        console.print(table)
        console.print()


def view_documents_by_code(console: Console, result: Any) -> None:
    """View documents grouped by code."""
    
    console.print("\n[bold cyan]Documents by Code[/bold cyan]\n")
    
    # Group by code
    docs_by_code: dict[str, list[Any]] = {}
    for dc in result.document_codes:
        if dc.code.name not in docs_by_code:
            docs_by_code[dc.code.name] = []
        docs_by_code[dc.code.name].append(dc)
    
    for code_name, doc_codes in sorted(docs_by_code.items()):
        console.print(f"[bold green]{code_name}[/bold green] ({len(doc_codes)} documents)")
        
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Document", style="dim")
        table.add_column("Rationale")
        
        for dc in doc_codes:
            table.add_row(dc.file_path.name, dc.rationale or "")
        
        console.print(table)
        console.print()


def show_code_book(console: Console, result: Any) -> None:
    """Display the code book."""
    
    console.print("\n[bold cyan]Code Book[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Code", style="cyan")
    table.add_column("Description")
    table.add_column("Criteria")
    
    for code in result.code_book.codes:
        table.add_row(code.name, code.description, code.criteria)
    
    console.print(table)


def show_statistics(console: Console, result: Any) -> None:
    """Display summary statistics."""
    
    console.print("\n[bold cyan]Summary Statistics[/bold cyan]\n")
    
    if result.mode == AnalysisMode.CODING:
        console.print(f"[bold]Total coded sentences:[/bold] {len(result.sentence_codes)}")
        
        # Count by code
        code_counts: dict[str, int] = {}
        for sc in result.sentence_codes:
            code_counts[sc.code.name] = code_counts.get(sc.code.name, 0) + 1
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Code", style="cyan")
        table.add_column("Count", justify="right", style="green")
        
        for code_name, count in sorted(code_counts.items(), key=lambda x: x[1], reverse=True):
            table.add_row(code_name, str(count))
        
        console.print(table)
    else:
        unique_docs = len(set(dc.file_path for dc in result.document_codes))
        console.print(f"[bold]Total coded documents:[/bold] {unique_docs}")
        
        # Count by code
        code_counts: dict[str, int] = {}
        for dc in result.document_codes:
            code_counts[dc.code.name] = code_counts.get(dc.code.name, 0) + 1
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Code", style="cyan")
        table.add_column("Count", justify="right", style="green")
        
        for code_name, count in sorted(code_counts.items(), key=lambda x: x[1], reverse=True):
            table.add_row(code_name, str(count))
        
        console.print(table)
