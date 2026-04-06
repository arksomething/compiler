def postprocess(opcodes: list[str]) -> list[str]:
    """Entry ``CALL main``; on return, ``JMP .exit`` so we do not fall into the next function. ``.exit`` at end."""
    return ["CALL main", "JMP .exit", *opcodes, ".exit"]
