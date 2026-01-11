# Modern Python Toolchain with `uv`

This project is set up with a modern Python toolchain using `uv` for package management, `ruff` for linting/formatting, and `pytest` for testing.

## 🚀 Quick Start

### 1. Install `uv`
`uv` is an extremely fast Python package installer and resolver, written in Rust. It's a drop-in replacement for `pip`, `pip-tools`, and `virtualenv`.

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Set Up the Project
Once `uv` is installed, you can create a virtual environment and install dependencies:

```bash
# Create a virtual environment
uv venv

# Activate it (Windows - Git Bash / PowerShell)
source .venv/Scripts/activate
# Activate it (macOS/Linux)
source .venv/bin/activate

# Install dependencies from pyproject.toml
uv pip install -e ".[dev]"
```

## 🛠️ Toolchain Usage

### Package Management
- **Add a dependency:** `uv add requests` (or manually add to `pyproject.toml` and run `uv pip install .`)
- **Sync environment:** `uv pip compile pyproject.toml -o requirements.txt` (optional, `uv` handles this internally for many tasks).

### Linting & Formatting (`ruff`)
`ruff` is an incredibly fast Python linter and code formatter.

- **Check linting:** `uv run ruff check .`
- **Fix linting errors:** `uv run ruff check --fix .`
- **Format code:** `uv run ruff format .`

### Testing (`pytest`)
- **Run tests:** `uv run pytest`

### Type Checking (`mypy`)
- **Run type check:** `uv run mypy src`

## 📂 Project Structure
- `src/`: Source code.
- `tests/`: Unit and integration tests.
- `pyproject.toml`: Project configuration and dependencies.

## Why this toolchain?
1. **Speed**: `uv` and `ruff` are written in Rust and are orders of magnitude faster than traditional Python tools.
2. **Simplicity**: `pyproject.toml` centralizes configuration for almost all tools.
3. **Reliability**: `uv` provides reproducible builds and efficient dependency resolution.

# compiler
