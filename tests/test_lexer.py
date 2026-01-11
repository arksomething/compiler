import io
from compiler.lexer import tokenize
from compiler.tokens import TokenType

def test_tokenize_basic():
    code = "fn main() { print(42) }"
    tokens = tokenize(io.StringIO(code))
    
    expected_types = [
        TokenType.FN, TokenType.IDENTIFIER, TokenType.LPAREN, TokenType.RPAREN,
        TokenType.LBRACE, TokenType.PRINT, TokenType.LPAREN, TokenType.NUMBER,
        TokenType.RPAREN, TokenType.RBRACE
    ]
    
    assert [t.type for t in tokens] == expected_types
    assert tokens[1].value == "main"
    assert tokens[7].value == "42"

def test_tokenize_operators():
    code = "x = 10 + 20 * 3 / 2 == 40 != 5 < 10 > 2"
    tokens = tokenize(io.StringIO(code))
    
    expected_types = [
        TokenType.IDENTIFIER, TokenType.EQUALS, TokenType.NUMBER, TokenType.ADD,
        TokenType.NUMBER, TokenType.MUT, TokenType.NUMBER, TokenType.DIV,
        TokenType.NUMBER, TokenType.EQEQ, TokenType.NUMBER, TokenType.NOTEQ,
        TokenType.NUMBER, TokenType.LT, TokenType.NUMBER, TokenType.GT,
        TokenType.NUMBER
    ]
    
    assert [t.type for t in tokens] == expected_types

def test_tokenize_strings():
    code = 'print("hello world")'
    tokens = tokenize(io.StringIO(code))
    
    assert tokens[0].type == TokenType.PRINT
    assert tokens[1].type == TokenType.LPAREN
    assert tokens[2].type == TokenType.STRING
    assert tokens[2].value == "hello world"
    assert tokens[3].type == TokenType.RPAREN

