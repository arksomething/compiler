import io

from compiler.generation import codegen
from compiler.ir import IRGenerator
from compiler.lexer import tokenize
from compiler.liveness import Liveness
from compiler.lowering import lower_ir
from compiler.parser import Parser
from compiler.processing import postprocess


def generate_ir(code):
    tokens = tokenize(io.StringIO(code))
    parser = Parser(tokens)
    ast = parser.parse_program()
    generator = IRGenerator()
    generator.generate(ast)
    return generator.lines


def analyze_ir(code):
    lowered = lower_ir(generate_ir(code))
    analyzed, _ = Liveness(lowered).analyze()
    return analyzed


def compile_program(code):
    lowered = lower_ir(generate_ir(code))
    analyzed, coloring = Liveness(lowered).analyze()
    return postprocess(codegen(analyzed, coloring), coloring)


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
    assert any("CALL alloc" in line for line in lowered)


def test_constant_propagation_folds_constants_and_removes_dead_lines():
    analyzed = analyze_ir(
        """
        fn main() {
            x = 1
            y = 2
            z = x + y
            return z
        }
        """
    )

    assert analyzed == ["FUNC main ()", "rax = CONST 3", "RET"]


def test_constant_propagation_keeps_constants_across_blocks():
    analyzed = analyze_ir(
        """
        fn main() {
            x = 1
            if (1 == 1) {
                y = x
            }
            return x
        }
        """
    )

    assert "rax = CONST 1" in analyzed


def test_end_to_end_pipeline_folds_constants_into_final_code():
    program = compile_program(
        """
        fn main() {
            x = 1
            y = 2
            z = x + y
            return z
        }
        """
    )

    assert program == [
        "LDI r5 0",
        "CALL main",
        "BRA exit",
        ".main",
        "LDI r0 3",
        "RET",
        ".exit",
    ]
