class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}
    
    def lookup(self, key):
        if key in self.vars:
            return self.vars[key]
        elif self.parent:
            return self.parent.lookup(key)
        raise NameError(key)

    def define(self, key, value):
        self.vars[key] = value
    
    def assign(self, key, value):
        if key in self.vars:
            self.vars[key] = value
            return True
        elif self.parent:
            return self.parent.assign(key, value)
        else:
            return False

class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value

class Function:
    def __init__(self, params, body, closure):
        self.params = params
        self.body = body
        self.closure = closure
            
class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.current_env = self.global_env
    
    def interpret(self, node):
        node_type = node.__class__.__name__
        if node_type == "ProgramNode":
            for function in node.functions:
                self.interpret(function)
            for statement in node.statements:
                self.interpret(statement)
        elif node_type == "FunctionNode":
            self.current_env.define(node.name, Function(node.params, node.statements, self.current_env))
        elif node_type == "AssignmentNode":
            value = self.interpret(node.expr)
            if not self.current_env.assign(node.name, value):
                self.current_env.define(node.name, value)
            return value
        elif node_type == "PrintNode":
            print(self.interpret(node.expr))
        elif node_type == "IfNode":
            if self.interpret(node.condition):
                for statement in node.statements:
                    self.interpret(statement)
        elif node_type == "WhileNode":
            while self.interpret(node.condition):
                for statement in node.statements:
                    self.interpret(statement)
        elif node_type == "ReturnNode":
            v = None if node.expr is None else self.interpret(node.expr)
            raise ReturnValue(v)
        elif node_type == "NumberNode":
            return int(node.value)
        elif node_type == "IdentifierNode":
            return self.current_env.lookup(node.name)
        elif node_type == "BinaryOpNode":
            left = self.interpret(node.left)
            right = self.interpret(node.right)
            if node.op == "+":
                return left + right
            if node.op == "-":
                return left - right
            if node.op == "*":
                return left * right
            if node.op == "/":
                return left // right
            if node.op == "==":
                return left == right
            if node.op == "!=":
                return left != right
            if node.op == "<":
                return left < right
            if node.op == ">":
                return left > right

        elif node_type == "CallNode":
            function = self.current_env.lookup(node.name)
            call_env = Environment(parent=function.closure)
            args = [self.interpret(arg) for arg in node.args]

            for param, arg in zip(function.params, args):
                call_env.define(param, arg)

            saved_env = self.current_env
            self.current_env = call_env

            try:
                for statement in function.body:
                    self.interpret(statement)
                return None
            except ReturnValue as ret:
                return ret.value
            finally:
                self.current_env = saved_env
        return None
