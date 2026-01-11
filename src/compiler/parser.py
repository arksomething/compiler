try:
    from .tokens import TokenType
    from .ast_nodes import (
        ProgramNode, FunctionNode, AssignmentNode, PrintNode, 
        IfNode, WhileNode, ReturnNode, NumberNode, 
        IdentifierNode, BinaryOpNode, CallNode
    )
except ImportError:
    from tokens import TokenType
    from ast_nodes import (
        ProgramNode, FunctionNode, AssignmentNode, PrintNode, 
        IfNode, WhileNode, ReturnNode, NumberNode, 
        IdentifierNode, BinaryOpNode, CallNode
    )

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.current_token = tokens[0] if tokens else None

    def advance(self):
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = None

    def expect(self, token_type):
        if self.current_token is None:
            raise SyntaxError(f"Expected {token_type}, but reached end of input")
        if self.current_token.type != token_type:
            raise SyntaxError(f"Expected {token_type}, got {self.current_token.type}")
        self.advance()

    def peek(self):
        if self.position + 1 < len(self.tokens):
            return self.tokens[self.position + 1]
        return None

    def parse_program(self):
        functions = []
        while self.current_token and self.current_token.type == TokenType.FN:
            functions.append(self.parse_function())
        statements = []
        while self.current_token is not None:
            statements.append(self.parse_statement())

        return ProgramNode(functions, statements)

    def parse_function(self):
        self.expect(TokenType.FN)
        name = self.current_token.value
        self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.LPAREN)
        params = []
        if self.current_token.type != TokenType.RPAREN:
            params.append(self.current_token.value)
            self.expect(TokenType.IDENTIFIER)
            while self.current_token.type == TokenType.COMMA:
                self.advance()
                params.append(self.current_token.value)
                self.expect(TokenType.IDENTIFIER)
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        
        statements = []
        while self.current_token.type != TokenType.RBRACE:
            statements.append(self.parse_statement())
        
        self.expect(TokenType.RBRACE)
        
        return FunctionNode(name, params, statements)

    def parse_statement(self):
        if self.current_token.type == TokenType.PRINT:
            return self.parse_print_stmt()
        elif self.current_token.type == TokenType.IF:
            return self.parse_if_stmt()
        elif self.current_token.type == TokenType.WHILE:
            return self.parse_while_stmt()
        elif self.current_token.type == TokenType.RETURN:
            return self.parse_return_stmt()
        elif self.current_token.type == TokenType.IDENTIFIER and self.peek() and self.peek().type == TokenType.EQUALS:
            return self.parse_assignment()
        else:
            return self.parse_expression()

    def parse_assignment(self):
        identifier = self.current_token.value
        self.advance()
        self.expect(TokenType.EQUALS)
        expr = self.parse_expression()
        return AssignmentNode(identifier, expr)

    def parse_print_stmt(self):
        self.expect(TokenType.PRINT)
        expr = self.parse_expression()
        return PrintNode(expr)

    def parse_if_stmt(self):
        self.expect(TokenType.IF)
        self.expect(TokenType.LPAREN)
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        statements = []
        while self.current_token.type != TokenType.RBRACE:
            statements.append(self.parse_statement())
        self.expect(TokenType.RBRACE)
        return IfNode(expr, statements)

    def parse_while_stmt(self):
        self.expect(TokenType.WHILE)
        self.expect(TokenType.LPAREN)
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        statements = []
        while self.current_token.type != TokenType.RBRACE:
            statements.append(self.parse_statement())
        self.expect(TokenType.RBRACE)
        return WhileNode(expr, statements)

    def parse_return_stmt(self):
        self.expect(TokenType.RETURN)
        return ReturnNode(self.parse_expression())

    def parse_expression(self):
        leftAddition = self.parse_addition()
        if self.current_token and self.current_token.type == TokenType.EQEQ:
            self.expect(TokenType.EQEQ)
            return BinaryOpNode("==", leftAddition, self.parse_addition())
        elif self.current_token and self.current_token.type == TokenType.NOTEQ:
            self.expect(TokenType.NOTEQ)
            return BinaryOpNode("!=", leftAddition, self.parse_addition())
        elif self.current_token and self.current_token.type == TokenType.GT:
            self.expect(TokenType.GT)
            return BinaryOpNode(">", leftAddition, self.parse_addition())
        elif self.current_token and self.current_token.type == TokenType.LT:
            self.expect(TokenType.LT)
            return BinaryOpNode("<", leftAddition, self.parse_addition())
        else:
            return leftAddition

    def parse_addition(self):
        left = self.parse_multiplication()
        
        while self.current_token and self.current_token.type in [TokenType.ADD, TokenType.SUB]:
            op = self.current_token.value
            self.advance()
            right = self.parse_multiplication()
            left = BinaryOpNode(op, left, right)
        
        return left

    def parse_multiplication(self):
        left = self.parse_primary()
        
        while self.current_token and self.current_token.type in [TokenType.MUT, TokenType.DIV]:
            op = self.current_token.value
            self.advance()
            right = self.parse_primary()
            left = BinaryOpNode(op, left, right)
        
        return left

    def parse_primary(self):
        if self.current_token is None:
            raise SyntaxError("Unexpected end of input")
            
        if self.current_token.type == TokenType.IDENTIFIER:
            if self.peek() and self.peek().type == TokenType.LPAREN:
                identifier = self.current_token.value
                self.advance()
                self.expect(TokenType.LPAREN)
                args = []
                if self.current_token and self.current_token.type != TokenType.RPAREN:
                    args.append(self.parse_expression())
                    while self.current_token and self.current_token.type == TokenType.COMMA:
                        self.advance()
                        args.append(self.parse_expression())

                self.expect(TokenType.RPAREN)
                return CallNode(identifier, args)
            else:
                identifier = self.current_token.value
                self.advance()
                return IdentifierNode(identifier)
        elif self.current_token.type == TokenType.NUMBER:
            number = self.current_token.value
            self.advance()
            return NumberNode(number)
        elif self.current_token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        else:
            raise SyntaxError(f"Unexpected token: {self.current_token}")

