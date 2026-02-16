# Contributing to Inductive Coder LangGraph

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Create a `.env` file with your OpenAI API key

## Development Workflow

### Running Tests

```bash
pytest tests/ -v
```

With coverage:
```bash
pytest tests/ --cov=inductive_coder --cov-report=html
```

### Code Quality

Before submitting a PR, ensure code quality:

```bash
# Format code
black inductive_coder tests

# Lint
ruff check inductive_coder tests

# Type checking
mypy inductive_coder
```

### Project Structure

```
inductive_coder/
├── domain/              # Business entities and interfaces
├── application/         # Use cases and workflows  
├── infrastructure/      # External implementations
└── presentation/        # CLI and UI
```

Follow Clean Architecture principles:
- Domain layer has no external dependencies
- Application layer depends only on domain
- Infrastructure implements domain interfaces
- Presentation depends on application and infrastructure

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints for all functions and methods
- Line length: 88 characters (Black default)
- Use docstrings for public APIs

### Type Hints

This project uses strict typing:

```python
def process_document(doc: Document) -> AnalysisResult:
    """Process a document and return analysis results."""
    ...
```

### Error Handling

- Use specific exceptions
- Provide clear error messages
- Handle expected errors gracefully

### Testing

- Write tests for new features
- Maintain or improve code coverage
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

Example:
```python
def test_code_book_operations() -> None:
    """Test code book add and retrieve operations."""
    # Arrange
    code_book = CodeBook()
    code = Code(name="Test", description="...", criteria="...")
    
    # Act
    code_book.add_code(code)
    
    # Assert
    assert len(code_book) == 1
    assert code_book.get_code("Test") == code
```

## Contributing Guidelines

### Reporting Issues

When reporting bugs, include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces

### Feature Requests

For new features:
- Describe the use case
- Explain why it's needed
- Suggest implementation approach (optional)
- Consider backward compatibility

### Pull Requests

1. Create a feature branch from `main`
2. Make your changes
3. Add/update tests
4. Update documentation
5. Ensure all tests pass
6. Submit PR with clear description

PR checklist:
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted (black)
- [ ] Linting passes (ruff)
- [ ] Type checking passes (mypy)
- [ ] All tests pass

### Commit Messages

Use clear, descriptive commit messages:

```
Add support for custom code book schemas

- Implement schema validation
- Add tests for schema parsing
- Update documentation

Fixes #123
```

## Areas for Contribution

### High Priority

- Additional LLM providers (Anthropic, Azure OpenAI, etc.)
- Web UI (Streamlit or Gradio)
- Export to common formats (CSV, Excel, SPSS)
- Batch processing improvements
- Performance optimizations

### Medium Priority

- Additional visualization options
- Code merging and refinement tools
- Inter-rater reliability calculations
- Integration with qualitative analysis software

### Documentation

- Tutorial videos
- Use case examples
- Best practices guide
- API documentation

## Architecture Decisions

When making significant changes, consider:

1. **SOLID Principles**: Keep code modular and testable
2. **Clean Architecture**: Maintain layer separation
3. **Token Efficiency**: Minimize LLM API costs
4. **User Experience**: Keep CLI intuitive and UI responsive
5. **Extensibility**: Design for future enhancements

## Questions?

- Open a GitHub issue for questions
- Check existing issues and discussions
- Review the USAGE.md guide

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Code of Conduct

- Be respectful and professional
- Welcome newcomers
- Focus on constructive feedback
- Prioritize project goals over personal preferences

Thank you for contributing!
