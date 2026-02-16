# Usage Guide

This guide provides detailed instructions for using the Inductive Coder LangGraph application.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Analysis Modes](#analysis-modes)
4. [Step-by-Step Tutorial](#step-by-step-tutorial)
5. [Advanced Usage](#advanced-usage)
6. [Architecture](#architecture)
7. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.12 or higher
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone https://github.com/konbraphat51/InductiveCoderLangGraph.git
cd InductiveCoderLangGraph
```

2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### Alternative: Using uv

If you have [uv](https://github.com/astral-sh/uv) installed:

```bash
uv sync
```

## Quick Start

1. Create a prompt file describing your research question:
```bash
python -m inductive_coder.main create-prompt-template -o my_prompt.md
# Edit my_prompt.md with your research context
```

2. Run analysis:
```bash
# Coding mode (sentence-level)
python -m inductive_coder.main analyze \
  --mode coding \
  --input-dir ./data \
  --prompt-file my_prompt.md \
  --output-dir ./output

# Categorization mode (document-level)
python -m inductive_coder.main analyze \
  --mode categorization \
  --input-dir ./data \
  --prompt-file my_prompt.md \
  --output-dir ./output
```

3. View results:
```bash
python -m inductive_coder.main ui --results-dir ./output
```

## Analysis Modes

### Coding Mode

**Purpose**: Apply codes to individual sentences within documents.

**Use when**:
- You need fine-grained analysis
- Different parts of documents represent different themes
- You want to identify specific quotes or passages

**Process**:
1. **Round 1**: LLM reads all documents and creates a code book
2. **Round 2**: 
   - Per document, decide whether to chunk (for token optimization)
   - Apply codes to sentences or chunks
   - Skip irrelevant chunks to save tokens

**Output**:
- Code book with definitions and criteria
- Sentence-level codes with rationales
- Aggregated views by file and by code

### Categorization Mode

**Purpose**: Categorize entire documents with codes.

**Use when**:
- Documents are thematically cohesive
- You want document-level classification
- Each document represents a distinct case or instance

**Process**:
1. **Round 1**: LLM reads all documents and creates a code book
2. **Round 2**: Apply codes to entire documents

**Output**:
- Code book with definitions and criteria
- Document-level codes with rationales
- Aggregated views by file and by code

## Step-by-Step Tutorial

### Example: Analyzing Customer Reviews

#### 1. Prepare Your Data

Create a directory with text or markdown files:

```
data/
├── review1.txt
├── review2.txt
└── review3.txt
```

Each file contains one customer review.

#### 2. Create a Research Prompt

```bash
python -m inductive_coder.main create-prompt-template -o customer_review_prompt.md
```

Edit `customer_review_prompt.md`:

```markdown
# Research Question

What factors influence customer satisfaction and repeat purchase intention?

# Context

Customer reviews from an e-commerce platform covering:
- Product quality
- Customer service
- Shipping and delivery
- Pricing

# Focus Areas

1. Positive experiences
2. Negative experiences
3. Service quality
4. Logistical factors
```

#### 3. Run Coding Analysis

```bash
python -m inductive_coder.main analyze \
  --mode coding \
  --input-dir ./data \
  --prompt-file customer_review_prompt.md \
  --output-dir ./results_coding
```

This will:
- Read all review files
- Generate a code book (e.g., "Positive Service", "Product Quality", "Logistics Issues")
- Apply codes to relevant sentences
- Save results to `./results_coding`

#### 4. View Results Interactively

```bash
python -m inductive_coder.main ui --results-dir ./results_coding
```

In the UI, you can:
- View codes applied to each file
- See all sentences with a specific code
- Browse the code book
- View statistics

#### 5. Export and Use Results

Results are saved as JSON files that can be imported into other tools:

- `code_book.json`: Code definitions
- `sentence_codes.json`: All coded sentences
- `summary.txt`: Human-readable summary

## Advanced Usage

### Using an Existing Code Book

If you already have a code book (e.g., from a previous analysis or created manually), skip Round 1:

```bash
python -m inductive_coder.main analyze \
  --mode coding \
  --input-dir ./new_data \
  --code-book-file ./results_coding/code_book.json \
  --output-dir ./results_new
```

### Manual Code Book Creation

Create a JSON file with this structure:

```json
{
  "mode": "coding",
  "context": "Your research context",
  "codes": [
    {
      "name": "Code Name",
      "description": "What this code represents",
      "criteria": "When to apply this code"
    }
  ]
}
```

### Batch Processing

Process multiple directories:

```bash
for dir in data1 data2 data3; do
  python -m inductive_coder.main analyze \
    --mode coding \
    --input-dir ./$dir \
    --prompt-file prompt.md \
    --output-dir ./results_$dir
done
```

## Architecture

### Clean Architecture Layers

```
inductive_coder/
├── domain/              # Core business logic
│   ├── entities.py      # Domain models
│   └── repositories.py  # Repository interfaces
├── application/         # Use cases
│   ├── use_cases.py     # Analysis workflow
│   ├── workflows.py     # LangGraph workflows
│   └── state.py         # State definitions
├── infrastructure/      # External implementations
│   ├── llm_client.py    # OpenAI integration
│   └── repositories.py  # File system storage
└── presentation/        # User interfaces
    ├── cli.py           # Command-line interface
    └── ui.py            # Interactive viewer
```

### LangGraph Workflows

#### Round 1: Code Book Creation

```
[Read Document] → (More docs?) → [Read Document]
                       ↓ No
                [Create Code Book] → [End]
```

#### Round 2 (Coding): Apply Codes

```
[Decide Chunking] → [Code Chunk] → (More chunks?) → [Code Chunk]
                                          ↓ No
                                    [Next Document] → (More docs?) → [Decide Chunking]
                                                            ↓ No
                                                          [End]
```

#### Round 2 (Categorization): Apply Codes

```
[Categorize Document] → (More docs?) → [Categorize Document]
                              ↓ No
                            [End]
```

## Troubleshooting

### OpenAI API Errors

**Problem**: "Invalid API key"
**Solution**: Check your `.env` file and ensure `OPENAI_API_KEY` is set correctly.

**Problem**: Rate limit errors
**Solution**: Add delays between requests or use a higher-tier API plan.

### Memory Issues

**Problem**: Out of memory with large documents
**Solution**: 
- Use chunking in coding mode (automatic)
- Process documents in smaller batches
- Reduce context in prompts

### Unexpected Codes

**Problem**: LLM generates irrelevant or too many codes
**Solution**:
- Make your prompt more specific
- Provide clearer focus areas
- Use an existing code book from a pilot run
- Adjust the temperature in `llm_client.py` (lower = more focused)

### Token Costs

To minimize token usage:
1. Use chunking in coding mode (automatic)
2. Be specific in your research question
3. Filter irrelevant documents before analysis
4. Consider using GPT-3.5-turbo for initial exploration

## Best Practices

1. **Start Small**: Test with 3-5 documents first
2. **Iterate on Prompts**: Refine your research question based on initial results
3. **Review Code Books**: Check the generated code book before Round 2
4. **Use Existing Code Books**: Reuse code books across similar datasets
5. **Document Your Process**: Keep notes on prompt iterations and decisions

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/konbraphat51/InductiveCoderLangGraph/issues
- Documentation: See README.md and this guide

## License

See LICENSE file for details.
