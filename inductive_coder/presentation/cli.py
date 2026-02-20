"""CLI interface for the inductive coder."""

import asyncio
from pathlib import Path
from typing import Optional
import sys

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from dotenv import load_dotenv

from inductive_coder.domain.entities import AnalysisMode, HierarchyDepth, CodeBook, Code
from inductive_coder.application.use_cases import AnalysisUseCase, CodeBookGenerationUseCase
from inductive_coder.infrastructure.repositories import (
    FileSystemDocumentRepository,
    JSONCodeBookRepository,
    JSONAnalysisResultRepository,
)
from inductive_coder.logger import setup_file_logging, teardown_file_logging, logger

# Load environment variables
load_dotenv()

app = typer.Typer(help="Inductive Coder - LLM-based inductive coding tool")
console = Console()


def display_code_book(code_book: CodeBook) -> None:
    """Display code book with hierarchical structure if applicable."""
    if code_book.hierarchy_depth == HierarchyDepth.FLAT:
        # Display as flat table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Code", style="cyan")
        table.add_column("Description")
        table.add_column("Criteria")
        
        for code in code_book.codes:
            table.add_row(code.name, code.description, code.criteria)
        
        console.print(table)
    else:
        # Display as hierarchical tree
        console.print(f"[bold]Hierarchical Code Structure (depth: {code_book.hierarchy_depth.value}):[/bold]\n")
        
        # Build tree
        tree = Tree("📚 [bold]Code Book[/bold]")
        
        # Add root codes first
        root_codes = code_book.get_root_codes()
        _add_codes_to_tree(tree, root_codes, code_book)
        
        console.print(tree)
        
        # Also show flat table for reference
        console.print("\n[dim]Flat view:[/dim]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Code", style="cyan")
        table.add_column("Parent", style="yellow")
        table.add_column("Description")
        table.add_column("Criteria")
        
        for code in code_book.codes:
            parent_name = code.parent_code_name or "-"
            table.add_row(code.name, parent_name, code.description, code.criteria)
        
        console.print(table)


def _add_codes_to_tree(tree_node: Tree, codes: list[Code], code_book: CodeBook) -> None:
    """Recursively add codes to tree."""
    for code in codes:
        # Create node for this code
        label = f"[cyan]{code.name}[/cyan]: {code.description}"
        code_node = tree_node.add(label)
        
        # Add criteria as sub-item
        code_node.add(f"[dim]Criteria: {code.criteria}[/dim]")
        
        # Add children recursively
        children = code_book.get_children(code.name)
        if children:
            _add_codes_to_tree(code_node, children, code_book)


@app.command()
def analyze(
    mode: str = typer.Option(..., "--mode", "-m", help="Analysis mode: coding or categorization"),
    input_dir: Path = typer.Option(..., "--input-dir", "-i", help="Directory containing documents to analyze"),
    prompt_file: Optional[Path] = typer.Option(None, "--prompt-file", "-p", help="File containing user prompt/context"),
    code_book_file: Optional[Path] = typer.Option(None, "--code-book-file", "-c", help="Existing code book (skip round 1)"),
    output_dir: Path = typer.Option("./output", "--output-dir", "-o", help="Output directory for results"),
    hierarchy_depth: str = typer.Option("1", "--hierarchy-depth", "-d", help="Code hierarchy depth: 1 (flat), 2 (two-level), or arbitrary (unlimited)"),
    batch_size: int = typer.Option(1, "--batch-size", "-b", help="Number of documents to read per LLM call in round 1 (default 1)"),
) -> None:
    """Run inductive coding analysis."""
    
    # Validate mode
    try:
        analysis_mode = AnalysisMode(mode.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid mode '{mode}'. Must be 'coding' or 'categorization'")
        sys.exit(1)
    
    # Validate hierarchy depth
    try:
        hierarchy = HierarchyDepth(hierarchy_depth.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid hierarchy depth '{hierarchy_depth}'. Must be '1', '2', or 'arbitrary'")
        sys.exit(1)
    
    # Validate input directory
    if not input_dir.exists():
        console.print(f"[red]Error:[/red] Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Load user context
    user_context = ""
    if prompt_file:
        if not prompt_file.exists():
            console.print(f"[red]Error:[/red] Prompt file not found: {prompt_file}")
            sys.exit(1)
        user_context = prompt_file.read_text(encoding="utf-8")
    else:
        console.print("[yellow]Warning:[/yellow] No prompt file specified. Using default context.")
        user_context = "Analyze the documents and identify key themes and patterns."
    
    # Validate code book if provided
    if code_book_file and not code_book_file.exists():
        console.print(f"[red]Error:[/red] Code book file not found: {code_book_file}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print("\n[bold cyan]Inductive Coding Analysis[/bold cyan]")
    console.print(f"Mode: [green]{analysis_mode.value}[/green]")
    console.print(f"Hierarchy Depth: [green]{hierarchy.value}[/green]")
    console.print(f"Batch Size: [green]{batch_size}[/green]")
    console.print(f"Input: [blue]{input_dir}[/blue]")
    console.print(f"Output: [blue]{output_dir}[/blue]")
    
    if code_book_file:
        console.print(f"Code Book: [blue]{code_book_file}[/blue] (skipping round 1)")
    else:
        console.print("Code Book: [yellow]Will be created in round 1[/yellow]")
    
    log_path = output_dir / "run.log"
    console.print(f"Log: [blue]{log_path}[/blue] (real-time)")
    console.print()
    
    # Set up real-time file logging
    file_handler = setup_file_logging(output_dir)
    
    def progress_callback(workflow_name: str, current: int, total: int) -> None:
        """Print progress to console."""
        if current == 0:
            console.print(f"\n[bold yellow]> {workflow_name} workflow[/bold yellow] (0/{total})"
                          f"  -> [dim]{log_path}[/dim]")
        elif current == total:
            console.print(f"[bold green]* {workflow_name} workflow complete[/bold green] ({total}/{total})")
        else:
            console.print(f"  [cyan]{workflow_name}[/cyan] {current}/{total}")
    
    # Run analysis
    try:
        # Create use case with repositories
        use_case = AnalysisUseCase(
            doc_repository=FileSystemDocumentRepository(),
            code_book_repository=JSONCodeBookRepository(),
            result_repository=JSONAnalysisResultRepository(),
        )
        
        # Execute with progress callback
        result = asyncio.run(
            use_case.execute(
                mode=analysis_mode,
                input_dir=input_dir,
                user_context=user_context,
                output_dir=output_dir,
                existing_code_book=code_book_file,
                hierarchy_depth=hierarchy,
                batch_size=batch_size,
                progress_callback=progress_callback,
            )
        )
        
        teardown_file_logging(file_handler)
        
        # Display results
        console.print("\n[bold green]✓ Analysis complete![/bold green]\n")
        
        # Show code book
        display_code_book(result.code_book)
        console.print()
        
        # Show summary
        if result.mode == AnalysisMode.CODING:
            console.print(f"[bold]Total coded sentences:[/bold] {len(result.sentence_codes)}")
            
            # Count by code
            code_counts: dict[str, int] = {}
            for sc in result.sentence_codes:
                code_counts[sc.code.name] = code_counts.get(sc.code.name, 0) + 1
            
            console.print("\n[bold]Sentences per code:[/bold]")
            for code_name, count in sorted(code_counts.items()):
                console.print(f"  {code_name}: {count}")
        else:
            console.print(f"[bold]Total coded documents:[/bold] {len(set(dc.file_path for dc in result.document_codes))}")
            
            # Count by code
            code_counts_doc: dict[str, int] = {}
            for dc in result.document_codes:
                code_counts_doc[dc.code.name] = code_counts_doc.get(dc.code.name, 0) + 1
            
            console.print("\n[bold]Documents per code:[/bold]")
            for code_name, count in sorted(code_counts_doc.items()):
                console.print(f"  {code_name}: {count}")
        
        console.print(f"\n[bold]Results saved to:[/bold] [blue]{output_dir}[/blue]")
        console.print(f"  - Code book: code_book.json")
        
        if result.mode == AnalysisMode.CODING:
            console.print(f"  - Codes: sentence_codes.json")
        else:
            console.print(f"  - Codes: document_codes.json")
        
        console.print(f"  - Summary: summary.txt")
        console.print(f"  - Run log: run.log")
        console.print("\n[dim]Run 'inductive-coder ui --results-dir {output_dir}' to view results interactively[/dim]")
        
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {e}"
        tb_str = traceback.format_exc()
        
        # Log error to file before tearing down
        logger.error("Analysis failed: %s", error_msg)
        logger.error("Traceback:\n%s", tb_str)
        
        teardown_file_logging(file_handler)
        console.print(f"\n[red]Error:[/red] {e}")
        console.print(tb_str)
        sys.exit(1)


@app.command()
def generate_codebook(
    mode: str = typer.Option(..., "--mode", "-m", help="Analysis mode: coding or categorization"),
    input_dir: Path = typer.Option(..., "--input-dir", "-i", help="Directory containing documents to analyze"),
    prompt_file: Optional[Path] = typer.Option(None, "--prompt-file", "-p", help="File containing user prompt/context"),
    output_file: Path = typer.Option("./code_book.json", "--output-file", "-o", help="Output file for code book"),
    hierarchy_depth: str = typer.Option("1", "--hierarchy-depth", "-d", help="Code hierarchy depth: 1 (flat), 2 (two-level), or arbitrary (unlimited)"),
    batch_size: int = typer.Option(1, "--batch-size", "-b", help="Number of documents to read per LLM call (default 1)"),
) -> None:
    """Generate code book only (Round 1 only) without applying codes."""
    
    # Validate mode
    try:
        analysis_mode = AnalysisMode(mode.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid mode '{mode}'. Must be 'coding' or 'categorization'")
        sys.exit(1)
    
    # Validate hierarchy depth
    try:
        hierarchy = HierarchyDepth(hierarchy_depth.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid hierarchy depth '{hierarchy_depth}'. Must be '1', '2', or 'arbitrary'")
        sys.exit(1)
    
    # Validate input directory
    if not input_dir.exists():
        console.print(f"[red]Error:[/red] Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Load user context
    user_context = ""
    if prompt_file:
        if not prompt_file.exists():
            console.print(f"[red]Error:[/red] Prompt file not found: {prompt_file}")
            sys.exit(1)
        user_context = prompt_file.read_text(encoding="utf-8")
    else:
        console.print("[yellow]Warning:[/yellow] No prompt file specified. Using default context.")
        user_context = "Analyze the documents and identify key themes and patterns."
    
    # Create output directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    console.print("\n[bold cyan]Code Book Generation (Round 1 Only)[/bold cyan]")
    console.print(f"Mode: [green]{analysis_mode.value}[/green]")
    console.print(f"Hierarchy Depth: [green]{hierarchy.value}[/green]")
    console.print(f"Batch Size: [green]{batch_size}[/green]")
    console.print(f"Input: [blue]{input_dir}[/blue]")
    console.print(f"Output: [blue]{output_file}[/blue]")
    
    log_path = output_file.parent / "run.log"
    console.print(f"Log: [blue]{log_path}[/blue] (real-time)")
    console.print()
    
    # Set up real-time file logging
    file_handler = setup_file_logging(output_file.parent)
    
    def progress_callback(workflow_name: str, current: int, total: int) -> None:
        """Print progress to console."""
        if current == 0:
            console.print(f"\n[bold yellow]▶ {workflow_name} workflow[/bold yellow] (0/{total})"
                          f"  → [dim]{log_path}[/dim]")
        elif current == total:
            console.print(f"[bold green]✓ {workflow_name} workflow complete[/bold green] ({total}/{total})")
        else:
            console.print(f"  [cyan]{workflow_name}[/cyan] {current}/{total}")
    
    # Run Round 1 only
    try:
        # Create use case
        use_case = CodeBookGenerationUseCase(
            doc_repository=FileSystemDocumentRepository(),
            code_book_repository=JSONCodeBookRepository(),
        )
        
        # Execute with progress callback
        code_book = asyncio.run(
            use_case.execute(
                mode=analysis_mode,
                input_dir=input_dir,
                user_context=user_context,
                output_path=output_file,
                hierarchy_depth=hierarchy,
                batch_size=batch_size,
                progress_callback=progress_callback,
            )
        )
        
        teardown_file_logging(file_handler)
        
        # Display results
        console.print("\n[bold green]✓ Code book generated![/bold green]\n")
        
        # Show code book
        display_code_book(code_book)
        console.print()
        
        console.print(f"[bold]Code book saved to:[/bold] [blue]{output_file}[/blue]")
        console.print(f"  - Run log: {log_path}")
        console.print("\n[dim]You can now use this code book with:")
        console.print(f"  inductive-coder analyze --mode {mode} --code-book-file {output_file} ...[/dim]")
        
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {e}"
        tb_str = traceback.format_exc()
        
        # Log error to file before tearing down
        logger.error("Code book generation failed: %s", error_msg)
        logger.error("Traceback:\n%s", tb_str)
        
        teardown_file_logging(file_handler)
        console.print(f"\n[red]Error:[/red] {e}")
        console.print(tb_str)
        sys.exit(1)


@app.command()
def ui(
    results_dir: Path = typer.Option(..., "--results-dir", "-r", help="Directory containing analysis results"),
) -> None:
    """Launch interactive UI to view analysis results."""
    
    if not results_dir.exists():
        console.print(f"[red]Error:[/red] Results directory not found: {results_dir}")
        sys.exit(1)
    
    try:
        from inductive_coder.presentation.ui import launch_ui
        launch_ui(results_dir)
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {e}"
        tb_str = traceback.format_exc()
        
        # Log error
        logger.error("UI launch failed: %s", error_msg)
        logger.error("Traceback:\n%s", tb_str)
        
        console.print(f"[red]Error:[/red] {e}")
        console.print(tb_str)
        sys.exit(1)


@app.command()
def create_prompt_template(
    output_file: Path = typer.Option("prompt_template.md", "--output", "-o", help="Output file path"),
) -> None:
    """Create a prompt template file."""
    
    template = """# Inductive Coding Prompt Template

## Research Question

[Describe your research question or the purpose of your analysis here]

## Context

[Provide any relevant context about the documents you're analyzing, such as:
- What type of documents they are (interviews, survey responses, field notes, etc.)
- The domain or topic area
- Any specific aspects you're interested in exploring]

## Focus Areas

[Optional: List specific themes, concepts, or aspects you want to pay attention to]

1. 
2. 
3. 

## Additional Instructions

[Optional: Any other guidance for the coding process]

"""
    
    output_file.write_text(template, encoding="utf-8")
    console.print(f"[green]✓[/green] Prompt template created: [blue]{output_file}[/blue]")
    console.print("\nEdit this file with your research question and context, then use it with:")
    console.print(f"[dim]inductive-coder analyze --mode coding --input-dir ./data --prompt-file {output_file}[/dim]")


if __name__ == "__main__":
    app()
