# Developer Setup

## Prerequisites
- Python 3.11 or newer
- Poetry for dependency management (`pipx install poetry` recommended)
- Git
- Optional: Visual Studio Build Tools (Windows) for compiling scientific packages

## Environment bootstrap
```powershell
# Install project dependencies
poetry install

# Activate virtual environment
poetry shell

# Run database migrations
poetry run alembic upgrade head

# Run initial verification
poetry run pytest
```

## Platform notes
- **Windows**: ensure `pipx` or Python is added to PATH; install `pyqt6-tools` only if Qt Designer is required.
- **macOS**: use Homebrew to install Python 3.11 (`brew install python@3.11`); grant application permissions for screen recording if using plot exports.
- **Linux**: install system Qt dependencies if packaging with PyInstaller (`sudo apt install libegl1 libxcb-cursor0`).

## Tooling
- `pre-commit` hooks enforce linting and formatting.
- `ruff` for lint checks; `black` for formatting.
- `mypy` for static typing; configure strict optionality over time.
- `pytest` as the testing framework (`pytest-qt` for UI tests).

## Common tasks
| Task | Command |
| --- | --- |
| Run type checks | `poetry run mypy src` |
| Run linting | `poetry run ruff check .` |
| Format code | `poetry run black .` |
| Launch placeholder app | `poetry run spectrallibrary` |
