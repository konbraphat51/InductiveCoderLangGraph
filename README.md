# Inductive Coder LangGraph

An LLM-based inductive coding tool built with LangGraph for qualitative research analysis.

## Features

- **Two Analysis Modes:**
  - **Coding Mode**: Sentence-level coding with intelligent chunking
  - **Categorization Mode**: Document-level categorization

- **Hierarchical Code Structure:**
  - **Flat (depth 1)**: Traditional flat code structure with no hierarchy
  - **Two-Level (depth 2)**: Parent-child relationships for organized coding
  - **Arbitrary Depth**: Unlimited hierarchy levels, decided by the LLM

- **Multi-Round Analysis with Optional Re-reading:**
  - **Initial Reading**: Read all files and create an initial code book
  - **Optional Re-reading Rounds**: Selectively refine the code book by re-reading documents and identifying missing codes
  - **Final Application**: Apply the refined codes based on the final code book

- **Smart Optimization:**
  - Intelligent text chunking to minimize LLM token usage
  - Skip irrelevant sections automatically
  - Batch processing: Read multiple documents per LLM call for faster analysis

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

# Optional: per-node model overrides
READ_DOCUMENT_MODEL=gpt-3.5-turbo
CREATE_CODEBOOK_MODEL=gpt-4-turbo-preview
DECIDE_CHUNKING_MODEL=gpt-3.5-turbo
CODE_CHUNK_MODEL=gpt-4-turbo-preview
CATEGORIZE_DOCUMENT_MODEL=gpt-4-turbo-preview
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

**With Hierarchical Codes**:
```bash
# Flat structure (default, no hierarchy)
uv run inductive-coder analyze \
  --mode coding \
  --hierarchy-depth 1 \
  --input-dir ./data \
  --prompt-file my_prompt.md \
  --output-dir ./output

# Two-level hierarchy (parent-child)
uv run inductive-coder analyze \
  --mode coding \
  --hierarchy-depth 2 \
  --input-dir ./data \
  --prompt-file my_prompt.md \
  --output-dir ./output

# Arbitrary depth (LLM decides)
uv run inductive-coder analyze \
  --mode coding \
  --hierarchy-depth arbitrary \
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

**Batch Processing** (read multiple documents per LLM call):
```bash
# Read documents in batches of 10 (faster, uses longer context)
uv run inductive-coder analyze \
  --mode coding \
  --batch-size 10 \
  --input-dir ./data \
  --prompt-file my_prompt.md \
  --output-dir ./output

# Default batch-size is 1 (one document per LLM call)
# Higher batch sizes are faster but may affect code consistency
# Recommended range: 1-20 depending on document length and LLM context limit
```

**Re-reading Rounds** (refine code book quality):
```bash
# Run with 2 additional re-reading rounds
uv run inductive-coder analyze \
  --mode coding \
  --input-dir ./data \
  --prompt-file my_prompt.md \
  --re-reading-rounds 2 \
  --output-dir ./output

# The re-reading process:
# 1. Initial reading: Create the first code book
# 2. Round 1 re-reading: Read documents again with the code book visible
#    to identify and note any missing codes or patterns
# 3. Update: Expand the code book with newly identified codes
# 4. Round 2 re-reading: Repeat the process to further refine
# 5. Final update: Create the refined code book for application

# For codebook generation only (no code application):
uv run inductive-coder generate-codebook \
  --mode coding \
  --input-dir ./data \
  --prompt-file my_prompt.md \
  --re-reading-rounds 1 \
  --output-file ./refined_codebook.json
```

**Create a manual code book**:
```bash
# Copy the template
cp codebook_template.json my_codebook.json

# Edit the file with your codes
# Then use it with --code-book-file option
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
