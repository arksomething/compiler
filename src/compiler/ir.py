class Environment:
    # needs to map vars to registers.
    def __init__(self, reg_allocator, parent=None):
        self._reg_allocator = reg_allocator
        self.parent = parent
        self.vars = {}
    
    def lookup(self, key):
        if key in self.vars:
            return self.vars[key]
        elif self.parent:
            return self.parent.lookup(key)
        raise NameError(key)

    def define(self, key):
        self.vars[key] = self._reg_allocator()
        return self.vars[key]
    

class IRGenerator:
    def __init__(self, output_path=None):
        self.output_path = output_path
        self.output_file = None
        self.lines = []
        self.reg = 0
        self.label = 0
        self.terminated = False
        self.current_env = Environment(self.new_register)
        if self.output_path:
            self.output_file = open(self.output_path, "w")
        
    def new_register(self):
        ret = self.reg
        self.reg += 1
        return f"r{ret}"

    def new_label(self):
        ret = self.label
        self.label += 1
        return f".{ret}"

    def emit(self, instruction):
        line = str(instruction)
        self.lines.append(line)
        if self.output_file:
            self.output_file.write(line + "\n")

    def generate(self, node):
        if self.terminated:
            return
        node_type = node.__class__.__name__
        if node_type == "ProgramNode":
            for function in node.functions:
                self.generate(function)
            for statement in node.statements:
                self.generate(statement)
        elif node_type == "FunctionNode":
            old_env = self.current_env
            new_env = Environment(self.new_register, parent=self.current_env)

            self.current_env = new_env
            params_str = ", ".join(node.params)
            self.terminated = False
            self.emit(f"FUNC {node.name} ({params_str})")
            i = 0
            for param in node.params:
                r = self.current_env.define(param)
                self.emit(f"{r} = ARG {i}")
                i += 1
            for statement in node.statements:
                self.generate(statement)
                
            self.terminated = False
            self.current_env = old_env
        elif node_type == "AssignmentNode":
            reg = self.generate(node.expr)
            dest = self.current_env.define(node.name)
            self.emit(f"{dest} = {reg}")
        
        elif node_type == "PrintNode":
            reg = self.generate(node.expr)
            self.emit(f"PRINT {reg}")
        elif node_type == "IfNode":
            condition = self.generate(node.condition)
            t = self.new_label()
            f = self.new_label()
            end = self.new_label()
            self.emit(f"BR {condition}, label {t}, label {f}")
            self.terminated = False
            self.emit(f"{t}:")
            for statement in node.statements:
                self.generate(statement)
            self.emit(f"JMP label {end}")
            self.terminated = False
            self.emit(f"{f}:")
            self.terminated = False
            self.emit(f"{end}:")
        elif node_type == "WhileNode":
            start = self.new_label()
            body = self.new_label()
            end = self.new_label()
            self.terminated = False
            self.emit(f"{start}:")
            condition = self.generate(node.condition)
            self.emit(f"BR {condition}, label {body}, label {end}")
            self.terminated = False
            self.emit(f"{body}:")
            for statement in node.statements:
                self.generate(statement)
            self.emit(f"JMP label {start}")
            self.terminated = False
            self.emit(f"{end}:")
        elif node_type == "ReturnNode":
            if node.expr is not None:
                reg = self.generate(node.expr)
                self.emit(f"RET {reg}")
            else:
                self.emit("RET")
            self.terminated = True
        elif node_type == "NumberNode":
            reg = self.new_register()
            self.emit(f"{reg} = CONST {int(node.value)}")
            return reg
        elif node_type == "IdentifierNode":
            return self.current_env.lookup(node.name)
        elif node_type == "BinaryOpNode":
            left = self.generate(node.left)
            right = self.generate(node.right)
            reg = self.new_register()
            self.emit(f"{reg} = {left} {node.op} {right}")
            # might not handle booleans correctly
            return reg

        elif node_type == "CallNode":
            args = [self.generate(arg) for arg in node.args]
            args_str = ", ".join(map(str, args))
            reg = self.new_register()
            self.emit(f"{reg} = CALL {node.name}({args_str})")
            return reg

    def close(self):
        if self.output_file:
            self.output_file.close()
