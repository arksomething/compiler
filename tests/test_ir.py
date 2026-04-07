import io

from compiler.ir import IRGenerator
from compiler.lexer import tokenize
from compiler.lowering import lower_ir
from compiler.parser import Parser


def generate_ir(code):
    tokens = tokenize(io.StringIO(code))
    parser = Parser(tokens)
    ast = parser.parse_program()
    generator = IRGenerator()
    generator.generate(ast)
    return generator.lines


def test_ir_while_assignment_reuses_variable_register():
    ir = generate_ir(
        """
        x = 0
        while (x < 3) {
            x = x + 1
        }
        print(x)
        """
    )

    x_reg = ir[1].split(" = ")[0]
    assignments_to_x = [line for line in ir if line.startswith(f"{x_reg} = ")]
    condition_line = next(line for line in ir if " < " in line)

    assert len(assignments_to_x) == 2
    assert f"= {x_reg} < " in condition_line
    assert ir[-1] == f"PRINT {x_reg}"


def test_lowering_handles_function_names_starting_with_a():
    ir = generate_ir(
        """
        fn alloc(n) {
            return n
        }

        fn main() {
            return alloc(1)
        }
        """
    )

    lowered = lower_ir(ir)

    assert lowered[0] == "FUNC alloc (n)"
    assert "CALL alloc" in lowered
