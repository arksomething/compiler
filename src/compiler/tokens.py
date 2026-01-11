from enum import Enum, auto

class TokenType(Enum):
    LBRACE = auto()
    RBRACE = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    # Operators
    ADD = auto()
    SUB = auto()
    MUT = auto()
    DIV = auto()
    EQUALS = auto()      # = (assignment)
    EQEQ = auto()        # == (comparison)
    NOTEQ = auto()       # !=
    LT = auto()          # <
    GT = auto()          # >
    # Keywords
    FN = auto()
    IF = auto()
    WHILE = auto()
    PRINT = auto()       # print keyword
    RETURN = auto()      # return keyword
    EOF = auto()         # end of file

class Token:
    def __init__(self, type: TokenType, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token(type={self.type.name}, value=\"{self.value}\")"

delineators = ["{", "}", "(", ")", ","]

delineatorTypes = {
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ",": TokenType.COMMA,
}

operators = ["+", "-", "*", "/", "=", "==", "!", "!=", "<", ">"]

operatorTypes = {
    "+": TokenType.ADD, 
    "-": TokenType.SUB, 
    "/": TokenType.DIV,
    "*": TokenType.MUT,
    "=": TokenType.EQUALS,
    "==": TokenType.EQEQ,
    "!=": TokenType.NOTEQ,
    "<": TokenType.LT,
    ">": TokenType.GT,
}

keywords = {
    "fn": TokenType.FN,
    "if": TokenType.IF,
    "while": TokenType.WHILE,
    "print": TokenType.PRINT,
    "return": TokenType.RETURN,
}

