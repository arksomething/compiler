# Examples

This directory collects the sample text files that were previously scattered in
the repo root.

- `language/`: general source-language examples and small scratch programs
- `cpu/`: backend-safe sample programs plus `CPU_PROGRAMS.md`

Typical commands from the repo root:

```bash
uv run python -m compiler examples/language/sample.txt
uv run python -m compiler examples/language/fib.txt
uv run python -m compiler examples/cpu/sum_to_12.txt
```
