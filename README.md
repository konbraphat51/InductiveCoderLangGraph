# Inductive Coder LangGraph

An LLM-based inductive coding tool built with LangGraph for qualitative research analysis.

## Features

- **Two Analysis Modes:**
  - **Coding Mode**: Sentence-level coding with intelligent chunking
  - **Categorization Mode**: Document-level categorization

- **Two-Round Analysis:**
  - **Round 1**: Read all files and create a code book
  - **Round 2**: Apply codes based on the code book

- **Smart Optimization:**
  - Intelligent text chunking to minimize LLM token usage
  - Skip irrelevant sections automatically

- **Interactive UI:**
  - Visualize codes per file
  - View all coded sentences grouped by code

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Or with dev dependencies
uv sync --all-extras
```

## Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
```

## Usage

### 1. Create a Prompt File

Use the template to create your analysis prompt:

```bash
cp prompt_template.md my_prompt.md
# Edit my_prompt.md with your research question and context
```

### 2. Run Analysis

**Coding Mode** (sentence-level coding):
```bash
uv run inductive-coder analyze \
  --mode coding \
  --input-dir ./data \
  --prompt-file my_prompt.md \
  --output-dir ./output
```

**Categorization Mode** (document-level):
```bash
uv run inductive-coder analyze \
  --mode categorization \
  --input-dir ./data \
  --prompt-file my_prompt.md \
  --output-dir ./output
```

**Start from Round 2** (with existing code book):
```bash
uv run inductive-coder analyze \
  --mode coding \
  --input-dir ./data \
  --code-book-file ./my_codebook.json \
  --output-dir ./output
```

### 3. View Results

Launch the interactive UI:
```bash
uv run inductive-coder ui --results-dir ./output
```

## Project Structure

```
inductive_coder/
├── domain/           # Core business entities and interfaces
├── application/      # Use cases and business logic
├── infrastructure/   # External implementations (LLM, file system)
├── presentation/     # CLI and UI
└── main.py          # Application entry point
```

## Architecture

This project follows Clean Architecture principles with SOLID design:

- **Domain Layer**: Pure business entities (CodeBook, Code, Sentence, Document)
- **Application Layer**: Use cases for coding and categorization workflows
- **Infrastructure Layer**: LangGraph agents, LLM clients, file repositories
- **Presentation Layer**: CLI interface and visualization UI

## Development

```bash
# Run tests
uv run pytest

# Type checking
uv run mypy inductive_coder

# Code formatting
uv run black inductive_coder
uv run ruff check inductive_coder

# Run with coverage
uv run pytest --cov=inductive_coder
```

## License

See LICENSE file for details.
