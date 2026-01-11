import io
from compiler.lexer import tokenize
from compiler.parser import Parser
from compiler.ast_nodes import ProgramNode, FunctionNode, AssignmentNode, PrintNode

def test_parse_simple_program():
    code = """
    x = 10
    print(x)
    """
    tokens = tokenize(io.StringIO(code))
    parser = Parser(tokens)
    ast = parser.parse_program()
    
    assert isinstance(ast, ProgramNode)
    assert len(ast.statements) == 2
    assert isinstance(ast.statements[0], AssignmentNode)
    assert ast.statements[0].name == "x"
    assert isinstance(ast.statements[1], PrintNode)

def test_parse_function():
    code = """
    fn add(a, b) {
        return a + b
    }
    """
    tokens = tokenize(io.StringIO(code))
    parser = Parser(tokens)
    ast = parser.parse_program()
    
    assert len(ast.functions) == 1
    func = ast.functions[0]
    assert func.name == "add"
    assert func.params == ["a", "b"]
    assert len(func.statements) == 1

