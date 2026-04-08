def postprocess(opcodes, coloring):
    return ["LDI r5 0", "CALL main", "BRA exit", *opcodes, ".exit"]
