def codegen(ir, coloring):
    """Wiring hook: ``ir`` is IR lines; ``coloring`` has register_colors and spilled_registers."""
    print(ir, coloring)