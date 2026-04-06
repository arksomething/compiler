# Toy Compiler in Python

A small educational compiler pipeline for a custom language with functions, control
flow, expressions, and recursion.

Running the CLI currently does all of the following in sequence:

1. Tokenize source text
2. Parse tokens into an AST
3. Interpret the AST (executes the program)
4. Generate IR
5. Run liveness analysis and register coloring/spill insertion
6. Pass IR and allocation data to the codegen hook

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

Do not add a top-level `main()` call. The backend wraps emitted bytecode with `CALL main` and `JMP .exit` (see `processing.postprocess`); a manual `main()` in source becomes a second `CALL main` in the IR and breaks control flow. The tree-walk interpreter still runs first and only executes **top-level** statements, so a file that only defines functions (like the snippet above) will not run `main` during interpretation unless you add other top-level code.

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
uv run python -m compiler.main sample.txt

# Try recursion example
uv run python -m compiler.main fib.txt

# Debug frontend stages
uv run python -m compiler.main sample.txt --tokens --ast
```

What you will see:

- Program output from the interpreter when the file has top-level statements that run (the example above only defines `fn main`; bytecode still enters `main` via `CALL main`, but the interpreter does not call it automatically)
- The IR plus register-allocation metadata printed by `codegen` (currently a stub)

## Development commands

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
uv run mypy src
```

## Project layout

- `src/compiler/lexer.py`: tokenizer
- `src/compiler/parser.py`: recursive-descent parser
- `src/compiler/ast_nodes.py`: AST node definitions
- `src/compiler/interpreter.py`: tree-walk interpreter with lexical scoping
- `src/compiler/ir.py`: IR generation
- `src/compiler/liveness.py`: CFG, liveness, interference graph, coloring/spilling
- `src/compiler/generation.py`: codegen wiring hook
- `tests/`: lexer, parser, and interpreter tests
- `sample.txt`, `fib.txt`: runnable example programs

## Current limitations

- No `else` branch support yet
- Strings are tokenized but not parsed/executed end-to-end
- Register allocator is intentionally simple (`k = 2` colors)
- Backend code generation is not implemented yet (stub output only)
