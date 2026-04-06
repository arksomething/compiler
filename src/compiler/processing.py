def postprocess(opcodes):
    return ["CALL main", "BRA exit", *opcodes, ".exit"]
