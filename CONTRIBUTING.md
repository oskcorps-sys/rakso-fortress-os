# Contributing to SDD+

Thank you for your interest in contributing to SDD+ (Specification-Driven Development Extended)! 

SDD+ is an open-source, LLM-agnostic governance framework for spec-first development. We welcome contributions from developers, architects, QA engineers, and anyone interested in improving software quality through specification-driven practices.

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please treat everyone with respect, listen actively, and collaborate constructively.

---

## Getting Started

### Prerequisites

- Python 3.13+
- Git
- pip (or uv for faster installs)

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/oskcorps-sys/sdd-plus.git
cd sdd-plus

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run tests to verify setup
pytest

# Run with coverage
pytest --cov=sdd --cov-report=html
open htmlcov/index.html
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming convention:
- `feature/` — New features or enhancements
- `fix/` — Bug fixes
- `refactor/` — Code refactoring
- `docs/` — Documentation updates
- `test/` — Test improvements

### 2. Make Your Changes

**Important: Follow SDD+ principles:**

- ✓ Write tests first (TDD encouraged)
- ✓ Keep cyclomatic complexity low (aim for A/B grades)
- ✓ Update docstrings for public APIs
- ✓ Run code quality checks locally before pushing

```bash
# Run tests
pytest

# Run linting
flake8 sdd/ tests/

# Run security checks
bandit -r sdd/

# Run coverage
pytest --cov=sdd --cov-report=term-missing
```

### 3. Commit Your Changes

Use [Conventional Commits](https://www.conventionalcommits.org/) for clear commit history:

```bash
git commit -m "feat: Add new metric query function

- Implements metrics.query_audits() for phase filtering
- Adds 3 test cases (100% coverage)
- Closes #42"
```

**Commit types:**
- `feat:` — New feature
- `fix:` — Bug fix
- `refactor:` — Code refactoring
- `test:` — Test improvements
- `docs:` — Documentation
- `perf:` — Performance improvements
- `ci:` — CI/CD changes

### 4. Push and Create a Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title (e.g., "Add metrics query filtering")
- Description of changes
- Link to any related issues (Closes #123)
- Screenshot/demo if UI changes

**PR Checklist:**
- [ ] Tests passing locally (`pytest`)
- [ ] Coverage maintained ≥ 85%
- [ ] No new security warnings (`bandit`)
- [ ] Code quality checks pass (`flake8`)
- [ ] Docstrings updated for new functions
- [ ] Commits follow conventional commits format
- [ ] CHANGELOG.md updated

### 5. Code Review

A maintainer will review your PR. Be open to feedback and discussion. We may ask for:
- Additional tests
- Documentation clarification
- Performance improvements
- Refactoring for consistency

Once approved, your PR will be merged! 🎉

---

## Project Structure

```
sdd-plus/
├── sdd/
│   ├── cli/                    # CLI commands (Typer)
│   │   ├── commands/
│   │   │   ├── audit.py       # Audit loop (tests, coverage, specs, contracts)
│   │   │   ├── validate.py    # Schema validation
│   │   │   ├── check_patterns.py  # File enforcement
│   │   │   └── ...
│   │   └── main.py
│   ├── schemas/                # Pydantic v2 models
│   ├── validators/             # Contract & state validators
│   ├── telemetry.py            # JSONL event logging
│   ├── git_integration.py      # Git helpers
│   ├── enforcement.py          # File pattern enforcement
│   └── web/                    # FastAPI dashboard (Phase 6)
├── tests/
│   ├── test_*.py              # Test files (261+ tests)
│   └── ...
├── AGENTS.yaml                 # Role authority matrix
├── pyproject.toml             # Project config
└── README.md
```

### Key Files

- **AGENTS.yaml** — Defines roles (auditor, implementer) and file access patterns
- **sdd/artifacts/PHASE_*_SPEC.yaml** — Phase specifications (binding)
- **sdd/artifacts/PHASE_*_AUDIT.yaml** — Audit records
- **.sdd-metrics/** — Telemetry JSONL (gitignored)

---

## Testing Guidelines

### Test Coverage

- Minimum: 85%
- Target: 90%+
- Check locally: `pytest --cov=sdd --cov-report=html`

### Test Structure

```python
# tests/test_my_feature.py

import pytest
from sdd.my_module import my_function

class TestMyFeature:
    """Tests for my_feature functionality."""
    
    def test_basic_case(self):
        """Test the happy path."""
        result = my_function("input")
        assert result == "expected"
    
    def test_edge_case_empty_input(self):
        """Test with empty input."""
        with pytest.raises(ValueError):
            my_function("")
    
    def test_type_validation(self):
        """Test type checking."""
        with pytest.raises(TypeError):
            my_function(123)  # expects str
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_validators.py

# Run specific test
pytest tests/test_validators.py::TestValidateContract::test_valid_contract

# Run with coverage
pytest --cov=sdd --cov-report=html --cov-report=term-missing

# Run with verbose output
pytest -v
```

---

## Code Quality Standards

### Cyclomatic Complexity

We use [radon](https://radon.readthedocs.io/) to measure complexity:

```bash
radon cc sdd/ -a  # Show complexity grades (A is best)
radon mi sdd/     # Maintainability index
```

**Target grades:**
- A (1-5): Best
- B (6-10): Good
- C (11-15): Acceptable
- D (16-20): Complex, consider refactoring
- E (21-30): Too complex, refactor required
- F (31+): Unacceptable

### Code Style

- **Formatter**: Use `black` (auto-formatting)
- **Linter**: `flake8` for style violations
- **Type hints**: Required for public APIs
- **Docstrings**: Google-style for functions

```python
def query_audits(phase: int | None = None) -> list[dict]:
    """Query audit records from telemetry.
    
    Args:
        phase: Optional phase number to filter by. If None, all phases.
    
    Returns:
        List of audit records as dicts with keys: timestamp, phase, verdict, etc.
    
    Raises:
        FileNotFoundError: If telemetry directory doesn't exist.
    """
```

### Security

We use [bandit](https://bandit.readthedocs.io/) to scan for security issues:

```bash
bandit -r sdd/
```

**Known acceptable patterns** (fail-open telemetry, try/except):
- B110: try/except/pass (intentional, telemetry must never crash)
- B603: subprocess with hardcoded args (safe, no user input)

---

## Documentation

### Updating README

- Keep Quick Start examples current
- Add new commands as they're released
- Document breaking changes

### CHANGELOG Format

```markdown
## [0.2.1] - 2026-05-23

### Added
- New metric query filtering functions
- Export metrics as CSV

### Fixed
- Validation error messages now more helpful
- Pydantic schema field shadowing warning

### Changed
- Refactored audit() function for maintainability
```

---

## Reporting Issues

Found a bug? Have a feature idea?

1. **Search existing issues** — May already be reported
2. **Create an issue** with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Environment (Python version, OS)
   - Screenshots/error messages if helpful

---

## Release Process

(Maintainers only)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.2.1`
4. Push tag: `git push origin v0.2.1`
5. Create GitHub Release from tag
6. Build and publish to PyPI: `python -m build && twine upload dist/*`

---

## Getting Help

- **Questions?** Open a GitHub Discussion
- **Bug report?** Create an Issue
- **Want to chat?** Check discussions or start a conversation

---

## License

By contributing to SDD+, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to SDD+! Together we're building better software through specification-driven development.** 🚀
