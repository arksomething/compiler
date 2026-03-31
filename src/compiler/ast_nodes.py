class ProgramNode:
    def __init__(self, functions, statements):
        self.functions = functions
        self.statements = statements

    def __repr__(self):
        return f"ProgramNode(functions={self.functions}, statements={self.statements})"

class FunctionNode:
    def __init__(self, name, params, statements):
        self.name = name
        self.params = params
        self.statements = statements

    def __repr__(self):
        return f"FunctionNode(name=\"{self.name}\", params={self.params}, statements={self.statements})"

class AssignmentNode:
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

    def __repr__(self):
        return f"AssignmentNode(name=\"{self.name}\", expr={self.expr})"

class PrintNode:
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"PrintNode(expr={self.expr})"

class IfNode:
    def __init__(self, condition, statements):
        self.condition = condition
        self.statements = statements

    def __repr__(self):
        return f"IfNode(condition={self.condition}, statements={self.statements})"

class WhileNode:
    def __init__(self, condition, statements):
        self.condition = condition
        self.statements = statements

    def __repr__(self):
        return f"WhileNode(condition={self.condition}, statements={self.statements})"

class ReturnNode:
    def __init__(self, expr=None):
        self.expr = expr

    def __repr__(self):
        return f"ReturnNode(expr={self.expr!r})"

class NumberNode:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"NumberNode(value={self.value})"

class IdentifierNode:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"IdentifierNode(name=\"{self.name}\")"

class BinaryOpNode:
    def __init__(self, op, left, right):
        self.op = op  # string: '+', '-', '*', '/', '==', '!=', '<', '>'
        self.left = left
        self.right = right

    def __repr__(self):
        return f"BinaryOpNode(op=\"{self.op}\", left={self.left}, right={self.right})"

class CallNode:
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __repr__(self):
        return f"CallNode(name=\"{self.name}\", args={self.args})"

