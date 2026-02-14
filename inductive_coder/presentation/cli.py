"""CLI interface for the inductive coder."""

import asyncio
from pathlib import Path
from typing import Optional
import sys

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from dotenv import load_dotenv

from inductive_coder.domain.entities import AnalysisMode
from inductive_coder.application.use_cases import AnalysisUseCase
from inductive_coder.infrastructure.repositories import (
    FileSystemDocumentRepository,
    JSONCodeBookRepository,
    JSONAnalysisResultRepository,
)

# Load environment variables
load_dotenv()

app = typer.Typer(help="Inductive Coder - LLM-based inductive coding tool")
console = Console()


@app.command()
def analyze(
    mode: str = typer.Option(..., "--mode", "-m", help="Analysis mode: coding or categorization"),
    input_dir: Path = typer.Option(..., "--input-dir", "-i", help="Directory containing documents to analyze"),
    prompt_file: Optional[Path] = typer.Option(None, "--prompt-file", "-p", help="File containing user prompt/context"),
    code_book_file: Optional[Path] = typer.Option(None, "--code-book-file", "-c", help="Existing code book (skip round 1)"),
    output_dir: Path = typer.Option("./output", "--output-dir", "-o", help="Output directory for results"),
) -> None:
    """Run inductive coding analysis."""
    
    # Validate mode
    try:
        analysis_mode = AnalysisMode(mode.lower())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid mode '{mode}'. Must be 'coding' or 'categorization'")
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
    console.print(f"Input: [blue]{input_dir}[/blue]")
    console.print(f"Output: [blue]{output_dir}[/blue]")
    
    if code_book_file:
        console.print(f"Code Book: [blue]{code_book_file}[/blue] (skipping round 1)")
    else:
        console.print("Code Book: [yellow]Will be created in round 1[/yellow]")
    
    console.print()
    
    # Run analysis
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running analysis...", total=None)
            
            # Create use case with repositories
            use_case = AnalysisUseCase(
                doc_repository=FileSystemDocumentRepository(),
                code_book_repository=JSONCodeBookRepository(),
                result_repository=JSONAnalysisResultRepository(),
            )
            
            # Execute
            result = asyncio.run(
                use_case.execute(
                    mode=analysis_mode,
                    input_dir=input_dir,
                    user_context=user_context,
                    output_dir=output_dir,
                    existing_code_book=code_book_file,
                )
            )
            
            progress.update(task, completed=True)
        
        # Display results
        console.print("\n[bold green]✓ Analysis complete![/bold green]\n")
        
        # Show code book
        console.print("[bold]Code Book:[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Code", style="cyan")
        table.add_column("Description")
        table.add_column("Criteria")
        
        for code in result.code_book.codes:
            table.add_row(code.name, code.description, code.criteria)
        
        console.print(table)
        console.print()
        
        # Show summary
        if result.mode == AnalysisMode.CODING:
            console.print(f"[bold]Total coded sentences:[/bold] {len(result.sentence_codes)}")
            
            # Count by code
            code_counts = {}
            for sc in result.sentence_codes:
                code_counts[sc.code.name] = code_counts.get(sc.code.name, 0) + 1
            
            console.print("\n[bold]Sentences per code:[/bold]")
            for code_name, count in sorted(code_counts.items()):
                console.print(f"  {code_name}: {count}")
        else:
            console.print(f"[bold]Total coded documents:[/bold] {len(set(dc.file_path for dc in result.document_codes))}")
            
            # Count by code
            code_counts = {}
            for dc in result.document_codes:
                code_counts[dc.code.name] = code_counts.get(dc.code.name, 0) + 1
            
            console.print("\n[bold]Documents per code:[/bold]")
            for code_name, count in sorted(code_counts.items()):
                console.print(f"  {code_name}: {count}")
        
        console.print(f"\n[bold]Results saved to:[/bold] [blue]{output_dir}[/blue]")
        console.print(f"  - Code book: code_book.json")
        
        if result.mode == AnalysisMode.CODING:
            console.print(f"  - Codes: sentence_codes.json")
        else:
            console.print(f"  - Codes: document_codes.json")
        
        console.print(f"  - Summary: summary.txt")
        console.print("\n[dim]Run 'inductive-coder ui --results-dir {output_dir}' to view results interactively[/dim]")
        
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback
        console.print(traceback.format_exc())
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
        console.print(f"[red]Error:[/red] {e}")
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
