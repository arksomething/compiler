import re
from pprint import pprint, pformat

REGEX_REGISTERS = re.compile(r'\b[rR]\d+\b')

class Liveness:
    def __init__(self, ir):
        self.ir = list(ir) if ir is not None else []

    def analyze(self):
        pprint(self.ir)
        self.parseNodes()
        self.cfg()
        return self.ir
    
    def parseNodes(self):
        blocks = []
        cur_block = []
        for i, line in enumerate(self.ir):
            if re.search(r'\b(JMP)|(RET)|(BR)\b', line):
                cur_block.append(line)
                blocks.append(cur_block)
                cur_block = []
            elif re.match(r'(\.\d+:)|(FUNC)', line):
                if cur_block:
                    blocks.append(cur_block)
                cur_block = []
                cur_block.append(line)
            else:
                cur_block.append(line)
        if cur_block:
            blocks.append(cur_block)

        self.nodes = [Node(block) for block in blocks]

    def cfg(self):
        labelToBlock = {}
        self.nodeMap = {f"b{i}":node for i, node in enumerate(self.nodes)}
        # print(self.nodeMap)
        for i, node in enumerate(self.nodes):
            if len(node.code) > 0 and re.match(r'\.\d+:', node.code[0]):
                m = re.match(r'\.\d+', node.code[0])
                if m:
                    labelToBlock[m.group(0)] = f"b{i}"

        for i, node in enumerate(self.nodes):
            for label in node.nextLabels:
                node.next.add(labelToBlock[label])

        if len(node.code) > 0 and not re.match(r"\b(JMP|RET|BR)\b", node.code[-1]):
            # must add the next one as well.
            if i != len(self.nodes) - 1:
                node.next.add(f"b{i + 1}")

        for node in self.nodes:
            print(node)

class Node:
    def __init__(self, code):
        self.code = code # arr of strings - the ir
        self.left = set()
        self.right = set()
        self.nextLabels = set()
        self.next = set()
        for i, line in enumerate(code):
            if len(line.split("=")) == 2:
                lhs, rhs = line.split("=", 1)
                self.left.update(REGEX_REGISTERS.findall(lhs))

                for reg in REGEX_REGISTERS.findall(rhs):
                    if 
                self.right.update(REGEX_REGISTERS.findall(rhs))
            elif len(line.split("=")) == 1:
                self.right.update(REGEX_REGISTERS.findall(line))

            if i == len(code) - 1:
                if re.search(r"\b(JMP|RET|BR)\b", line):
                    self.nextLabels = set(re.findall(r"\.\d+", line))

    def __repr__(self):
        head = self.code[0] if self.code else "?"
        return f"Node({head!r} left={self.left} right={self.right} next={list(self.next)})"



# class CodeBlock:
#     def __init__(self, code, next):

