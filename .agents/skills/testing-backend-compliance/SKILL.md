---
name: testing-backend-compliance
description: Test backend-only compliance fixes (GDPR, DORA, EU AI Act) in Apache Superset. Use when verifying model property changes, audit logging, or PII masking.
---

# Testing Backend Compliance Fixes in Superset

## Overview
Backend compliance fixes (e.g., GDPR PII masking, DORA audit logging) typically modify Python model properties or utility functions. These are shell-only tests — no browser/UI interaction needed, no recording needed.

## Environment Setup

### Full pytest (preferred)
```bash
# Install all dependencies
pip install -e ".[testing]"
# Or from requirements
pip install -r requirements/base.txt -r requirements/development.txt

# Run specific tests
python -m pytest tests/unit_tests/models/sql_lab_test.py -k "test_name" -v
```

### Dependency Conflicts
Superset has a deep import chain (`superset/__init__.py` → `superset/app.py` → `superset/extensions/` → celery, simplejson, flask-talisman, etc.). If `pip install -e .` fails with dependency conflicts, use the AST extraction fallback below.

### Fallback: AST-based source extraction
When full pytest import chain fails, extract and test the actual function source directly:
```python
import ast
with open('superset/models/sql_lab.py') as f:
    source = f.read()
tree = ast.parse(source)
# Walk AST to find target function, compile and execute in isolation
```
This validates the exact production code without needing the full app import chain.

## Pre-commit
- Always run `pre-commit install` after cloning
- `SKIP=ruff,pylint git commit` may be needed if pre-existing lint errors exist in touched files
- mypy, auto-walrus, formatting hooks work without full app deps

## Test File Patterns
- Model tests: `tests/unit_tests/models/sql_lab_test.py`
- Use `@pytest.mark.parametrize` for edge case coverage
- Use `MagicMock()` for model relationships (e.g., `query.user = MagicMock()`)
- Follow existing test patterns in the same file

## Devin Secrets Needed
None — backend-only model tests require no credentials or API keys.
