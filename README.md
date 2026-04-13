# Toy Compiler in Python

A small compiler for a custom language with functions, control flow, expressions, recursion, and an assembly-like backend.

Generally, this repo was written code-agent free with the exception of uninteresting tasks like wiring imports, README.md changes, or mass assembly/regex changes. 

For a language-focused reference, see `LANGUAGE.md`.

Running the CLI by default does all of the following in sequence:

1. Tokenize source text
2. Parse tokens into an AST
3. Generate IR
4. Lower IR for the backend calling convention
5. Run constant propagation, dead-code cleanup, liveness analysis, register coloring, and spill insertion
6. Emit assembly-like backend code

If you want the tree-walking interpreter instead, run the CLI with `--interpret`.

This repo stops at emitted assembly-like backend text. The assembler and CPU
implementation live in the separate FPGA repo:
`https://github.com/arksomething/fpga`.

## Language at a glance

### Supported constructs

- Function declarations: `fn name(param1, param2) { ... }`
- Variable assignment: `x = 42`
- Printing: `print(expr)`
- Conditionals: `if (condition) { ... }`
- Loops: `while (condition) { ... }`
- Returns: `return` and `return expr`
- Function calls: `f(1, 2)`

### Expressions and operators

- Integer literals (for example `10`)
- Identifiers
- Parenthesized expressions
- Arithmetic: `+`, `-`, `*`, `/` (integer division)
- Comparisons: `==`, `!=`, `<`, `>`

### Example program

```txt
fn fib(n) {
    if (n < 2) {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

fn main() {
    print(fib(10))
    return
}
```

## Quick start

### Requirements

- Python 3.10+
- `uv` ([installation docs](https://docs.astral.sh/uv/getting-started/installation/))

### Setup

```bash
uv venv
source .venv/bin/activate  # macOS/Linux
# source .venv/Scripts/activate  # Windows PowerShell/Git Bash
uv pip install -e ".[dev]"
```

You can also skip activation and use `uv run ...` for all commands.

## Run the compiler

```bash
# Run a program
uv run python -m compiler examples/language/sample.txt

# Try recursion example
uv run python -m compiler examples/language/fib.txt

# Debug frontend stages
uv run python -m compiler examples/language/sample.txt --tokens --ast

# Run the interpreter only
uv run python -m compiler examples/language/sample.txt --interpret
```

More sample inputs live under `examples/`, including backend-safe programs
documented in `examples/cpu/CPU_PROGRAMS.md`.

What you will see:

- By default, emitted assembly-like backend code that starts at `main`
- Interpreter output only when you explicitly pass `--interpret`
- For backend-oriented examples, prefer files under `examples/cpu/`
- Assembly emission only: assembling/running that output happens in the FPGA repo at `https://github.com/arksomething/fpga`

## Development commands

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
uv run mypy src
```

## Project layout

- `src/compiler/__main__.py`: package entrypoint for `python -m compiler`
- `src/compiler/cli.py`: CLI pipeline wiring
- `src/compiler/lexer.py`: tokenizer
- `src/compiler/parser.py`: recursive-descent parser
- `src/compiler/ast_nodes.py`: AST node definitions
- `src/compiler/interpreter.py`: tree-walk interpreter with lexical scoping
- `src/compiler/ir.py`: IR generation
- `src/compiler/liveness.py`: CFG, constant propagation, dead-code cleanup, liveness, interference graph, coloring/spilling
- `src/compiler/generation.py`: backend code generation
- `tests/`: lexer, parser, and interpreter tests
- `examples/`: organized source-language and backend-safe sample programs

## Current limitations

- No `else` branch support yet
- Strings are tokenized but not parsed/executed end-to-end
- `print(...)` is interpreter-visible, but currently lowers to `NOP` in backend output
- `*`, `/`, and `!=` are parsed by the front end, but are not fully lowered by the current backend
- The backend output is emitted as assembly-like text only; the assembler and CPU implementation live in the separate FPGA repo: `https://github.com/arksomething/fpga`
