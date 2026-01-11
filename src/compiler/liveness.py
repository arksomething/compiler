import re
REGEX_REGISTERS = re.compile(r'\b[rR]\d+\b')

class Liveness:
    def __init__(self, ir):
        return

class Node:
    def __init__(self, code, next):
        self.code = code
        if len(code.split("=")) == 2:
            self.left = REGEX_REGISTERS.findall(code.split("=")[0])
            self.right = REGEX_REGISTERS.findall(code.split("=")[1])
        else if len(code.split("=")) == 1:
            self.right = REGEX_REGISTERS.findall(code)
        
        self.next = next

