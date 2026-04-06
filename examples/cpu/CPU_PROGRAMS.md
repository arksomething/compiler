# CPU-Friendly Compiler Programs

These sample programs are written for the source language documented in
`README.md` and `LANGUAGE.md`, but they intentionally stay within the subset
that the current FPGA backend lowers cleanly.

Run them from the repo root with commands like:

```bash
uv run python -m compiler examples/cpu/sum_to_12.txt
```

## Backend-safe subset

- define a `fn main()` entry point
- do not add a top-level `main()` call
- prefer `return expr` from `main` so the final value lands in `r0`
- use `+`, `-`, `==`, `<`, and `>` for arithmetic/control flow
- use functions, loops, and conditionals

## Avoid for now

- `*` and `/`: parsed by the front end, but not lowered by `generation.py`
- `!=`: parsed by the front end, but not lowered by `generation.py`
- `print(...)` if you care about FPGA-visible output: it currently lowers to `NOP`
- recursion: accepted by the front end, but not part of this verified CPU sample set
- calls inside hot loops or higher-arity examples until the backend/core path is exercised more

## Sample files

- `sum_to_12.txt`: iterative triangular sum; `main()` returns `78`
- `iter_fib_11.txt`: iterative Fibonacci; `main()` returns `89`
- `pow2_loop.txt`: repeated doubling; `main()` returns `64`
- `sum_evens_10.txt`: sum of even numbers from `0` to `10`; `main()` returns `30`
- `max2_demo.txt`: two-argument comparison helper; `main()` returns `14`
- `sub_demo_40_17.txt`: simple subtraction helper; `main()` returns `23`
- `const42_main.txt`: minimal constant-return example; `main()` returns `42`
- `safe_hardware.txt`: combined smoke-test style program that prints several
  backend-safe helper results
