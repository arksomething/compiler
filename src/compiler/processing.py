def postprocess(opcodes: list[str]) -> list[str]:
    """Entry ``CALL main``; on return, ``BRA exit`` (label key matches ``.exit`` → ``exit`` in FPGA asm). ``.exit`` at end."""
    return ["CALL main", "BRA exit", *opcodes, ".exit"]
