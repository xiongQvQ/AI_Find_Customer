# Contributing to AI Hunter

Thank you for your interest in contributing! This document covers how to set up a development environment, run tests, and submit changes.

## Development Setup

```bash
# Clone and set up backend
git clone https://github.com/your-org/ai-hunter.git
cd ai-hunter/backend

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in at least LLM_MODEL, OPENAI_API_KEY, SERPER_API_KEY
```

## Running Tests

```bash
cd backend

# Full suite (443 tests, ~8s, no API calls needed)
python -m pytest tests/ -q

# Specific modules
python -m pytest tests/test_agents/ -v
python -m pytest tests/test_tools/ -v

# With coverage
python -m pytest tests/ --cov=. --cov-report=term-missing
```

All tests use mocks — no real API keys are required to run the test suite.

## Code Style

- Python: follow existing style (no formatter enforced yet, but keep consistent)
- No trailing whitespace, Unix line endings
- Docstrings on all public functions and classes
- Type hints on all function signatures

## Pull Request Guidelines

1. Fork the repo and create a feature branch: `git checkout -b feat/my-feature`
2. Write or update tests for your change
3. Ensure all 443 tests pass: `python -m pytest tests/ -q`
4. Keep PRs focused — one feature or fix per PR
5. Write a clear PR description explaining what changed and why

## Project Structure

See [README.md](README.md#project-structure) for a full directory overview.

## Key Design Decisions

- **Dual-model pattern**: use `reasoning_model` for ReAct agents that need multi-step tool decisions; use `llm_model` for single-shot extraction tasks
- **ReAct via `react_runner.py`**: all ReAct loops go through `react_loop()` — do not implement custom loops in agents
- **JSON output validation**: all LLM outputs must go through `parse_json()` + `validate_dict()` from `tools/llm_output.py`
- **Concurrency**: use `asyncio.Semaphore` from settings — never hardcode concurrency limits
- **No side effects in tools**: tool functions must be pure async functions with no global state mutations

## Reporting Issues

Please open a GitHub issue with:
- A clear description of the bug or feature request
- Steps to reproduce (for bugs)
- Expected vs actual behaviour
- Python version, OS, and relevant env vars (redact API keys)
