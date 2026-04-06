# Language Guide

This document describes the source language implemented by this toy compiler.
It focuses on the language as it exists today, including a few important
implementation quirks.

## Overview

The language is a small, brace-based language with:

- integer values
- variables created by assignment
- functions and recursion
- `if` and `while`
- `print`
- `return`

It is intentionally minimal. The current implementation is best thought of as
an educational language front end plus a partially wired backend pipeline.

## File Structure

A source file is parsed as:

1. zero or more function declarations
2. zero or more top-level statements

That means all `fn` declarations must come before any top-level statements.
Nested function declarations are not supported.

Example:

```txt
fn add(a, b) {
    return a + b
}

fn main() {
    print(add(2, 3))
    return
}
```

## Lexical Elements

### Keywords

- `fn`
- `if`
- `while`
- `print`
- `return`

### Delimiters

- `{` and `}`
- `(` and `)`
- `,`

### Operators

- assignment: `=`
- arithmetic: `+`, `-`, `*`, `/`
- comparison: `==`, `!=`, `<`, `>`

### Literals and names

- integer literals such as `0`, `7`, and `42`
- identifiers such as `x`, `total`, and `fib`

Whitespace is mostly insignificant, and semicolons are not used.

Strings are tokenized by the lexer, but they are not part of the usable source
language yet because the parser and runtime do not support them end-to-end.

## Grammar Snapshot

The current grammar is roughly:

```txt
program      := function* statement*
function     := "fn" IDENT "(" [IDENT ("," IDENT)*] ")" "{" statement* "}"

statement    := assignment
              | print_stmt
              | if_stmt
              | while_stmt
              | return_stmt
              | expr

assignment   := IDENT "=" expr
print_stmt   := "print" expr
if_stmt      := "if" "(" expr ")" "{" statement* "}"
while_stmt   := "while" "(" expr ")" "{" statement* "}"
return_stmt  := "return" [expr]

expr         := addition [("==" | "!=" | "<" | ">") addition]
addition     := multiplication (("+" | "-") multiplication)*
multiplication := primary (("*" | "/") primary)*
primary      := NUMBER
              | IDENT
              | IDENT "(" [expr ("," expr)*] ")"
              | "(" expr ")"
```

Two practical notes about this grammar:

- `print` takes any expression, so `print(1 + 2)` is common, but `print 1 + 2`
  also fits the parser.
- Comparison operators are only parsed once at the outer expression level, so
  chained comparisons like `a < b < c` are not supported.

## Statements

### Assignment

Variables are introduced by assignment. There is no separate declaration syntax.

```txt
x = 10
y = x + 5
```

### Print

`print` evaluates an expression and writes the result.

```txt
print(x)
print(1 + 2 * 3)
```

### If

`if` executes its block when the condition is truthy.

```txt
if (n < 2) {
    print(n)
}
```

There is no `else` branch yet.

### While

`while` repeats while its condition is truthy.

```txt
i = 0
while (i < 3) {
    print(i)
    i = i + 1
}
```

### Return

`return expr` returns a value from a function.

`return` by itself returns no value.

```txt
return x + 1
return
```

In practice, `return` should be used inside functions.

### Expression Statements

A bare expression is also a valid statement. This is mostly useful for function
calls whose return value you want to ignore.

```txt
do_work(5)
```

## Expressions

### Supported forms

- integer literals
- variable references
- parenthesized expressions
- named function calls
- binary arithmetic and comparisons

### Precedence

From highest to lowest:

1. parenthesized expressions and function calls
2. `*` and `/`
3. `+` and `-`
4. `==`, `!=`, `<`, `>`

Examples:

```txt
1 + 2 * 3        # parsed as 1 + (2 * 3)
(1 + 2) * 3
n - 1
fib(n - 1) + fib(n - 2)
```

### Numeric behavior

- numbers are integers
- `/` uses integer division
- there are no boolean literals; comparisons produce values used by control flow

Unary operators are not implemented yet, so negative literals must be expressed
through subtraction, for example `0 - 3`.

## Functions and Scope

Functions use the form:

```txt
fn name(param1, param2) {
    ...
}
```

Important runtime rules:

- function calls create a new function scope
- parameters are bound inside that new scope
- `if` blocks and `while` blocks do not create a new scope
- assignment updates the nearest existing binding, otherwise it creates a new
  binding in the current function or global scope

In the tree-walk interpreter, functions can read and update outer bindings that
already exist. In practice, that mostly means globals.

## Truthiness

Any expression can be used as an `if` or `while` condition.

The language currently behaves like this:

- zero is false
- non-zero is true
- comparison results are suitable for conditions

The interpreter uses Python truthiness internally, while the lowered backend
branching logic treats zero as false and non-zero as true.

## How Programs Run In This Repo

Running:

```bash
uv run python -m compiler your_file.txt
```

goes through these stages:

1. the lexer tokenizes the source
2. the parser builds an AST
3. the interpreter registers all functions, then executes top-level statements
4. IR is generated
5. IR is lowered and analyzed for liveness/register allocation
6. codegen emits the current assembly-like output

Two execution details matter a lot:

### `main` is the backend entry point

Postprocessing currently prepends a `CALL main` before emitted code, so the
backend assumes a `fn main()` exists.

### Top-level statements are interpreter-only in practice

Top-level statements do run in the tree-walk interpreter stage, but the emitted
backend output jumps directly into `main` and then exits. So top-level
statements are useful for interpreter experiments, but they are not the real
compiled entry point.

Because of that, source files meant for the backend should define `fn main()`
and should not add a manual top-level `main()` call.

## Example Program

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

This example shows:

- function declaration
- recursion
- arithmetic expressions
- comparison in an `if`
- `print`
- explicit `return`

## Current Limitations

The language implementation is intentionally incomplete. Current limitations
include:

- no `else`
- no strings in the parser/runtime, even though the lexer recognizes them
- no comments
- no unary operators such as unary minus
- no chained comparisons
- no nested function declarations
- no strict function-arity checking
- backend flow assumes `main` exists
