import io
import pytest
from compiler.lexer import tokenize
from compiler.parser import Parser
from compiler.interpreter import Interpreter

def run_code(code):
    tokens = tokenize(io.StringIO(code))
    parser = Parser(tokens)
    ast = parser.parse_program()
    interpreter = Interpreter()
    return interpreter.interpret(ast)

def test_interpreter_arithmetic(capsys):
    run_code("print(1 + 2 * 3)")
    captured = capsys.readouterr()
    assert captured.out.strip() == "7"

def test_interpreter_variables(capsys):
    run_code("""
    x = 10
    y = 20
    print(x + y)
    """)
    captured = capsys.readouterr()
    assert captured.out.strip() == "30"

def test_interpreter_function_call(capsys):
    run_code("""
    fn square(x) {
        return x * x
    }
    print(square(5))
    """)
    captured = capsys.readouterr()
    assert captured.out.strip() == "25"

def test_interpreter_recursion(capsys):
    run_code("""
    fn fact(n) {
        if (n == 0) { return 1 }
        return n * fact(n - 1)
    }
    print(fact(5))
    """)
    captured = capsys.readouterr()
    assert captured.out.strip() == "120"

def test_interpreter_while_loop(capsys):
    run_code("""
    i = 0
    while (i < 3) {
        print(i)
        i = i + 1
    }
    """)
    captured = capsys.readouterr()
    assert captured.out.strip() == "0\n1\n2"

