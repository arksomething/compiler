class roller:
    def roll(sell, node):
        node_type = node.__class_main.__name__

        if node_type == "ProgramNode":
            new_funcs = []
            new_statements = []
            for function in node.functions:
                new_funcs.append(self.roll(function))
            for statement in node.statements:
                new_statements.append(self.roll(statement))
            
            return ProgramNode(new_funcs, new_statements)
        elif node_type == "FunctionNode":
            new_statements = []
            new_params = []

            for param in node.params:
                new_params.append(self.roll(param))
            for statement in node.statements:
                new_statements.append(self.roll(statement))

            return FunctionNode(node.name, new_params, new_statements)
        elif node_type == "PrintNode":
            return PrintNode(self.roll(node.expr))

        elif node_type == "LoadNode":
            return node
        elif node_type == "StoreNode":
            return StoreNode()
