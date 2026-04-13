import re
from collections import defaultdict

REGISTER_OPERAND = re.compile(r"^(?:r\d+|s[56])\b")


def _physical_reg_number(base: str, color_map: dict) -> int:
    """Map IR register name to hardware register index (0..7)."""
    if base == "rax":
        return 0
    if base == "rsp":
        return 7
    if base == "s5":
        return 5
    if base == "s6":
        return 6
    return color_map[base] + 1


def codegen(ir, coloring):
    func_regs = defaultdict(list)
    arg_n = 0
    output = []

    for i, line in enumerate(ir):
        if not line:
            continue

        # Split on comma too so ``r4,`` does not stick to registers (e.g. ``CALL f(r4, r5)``).
        split = re.split(r"[(),\s]+", line)
        isAssignment = len(split) > 1 and split[1] == "="
        first = split[0]
        if not first:
            continue
        third = split[2] if len(split) > 2 else None
        fourth = split[3] if len(split) > 3 else None
        fifth = split[4] if len(split) > 4 else None

        if first[0] == ".":
            output.append(line[:-1])
        elif first == "FUNC":
            output.append("." + split[1])
        elif first == "RET":
            if len(split) > 1 and split[1]:
                output.append(f"MOV rax {split[1]}")
            output.append("RET")
        elif first == "JMP":
            parts = [p for p in split if p]
            target = parts[-1].rstrip(",") if len(parts) > 1 else third
            if target.startswith("."):
                output.append(f"BRA {target[1:]}")
            else:
                output.append(f"JMP {target}")
        elif first == "CALL":
            callee = split[1] if len(split) > 1 else ""
            output.append("CALL " + callee)
        elif third == "CALL":
            callee = fourth if fourth else ""
            output.append("CALL " + callee)
        elif fourth == "+":
            if REGISTER_OPERAND.match(fifth):
                output.append(f"ADD {first} {third} {fifth}")
            else:
                if int(fifth) != 0 or first != third:
                    output.append(f"ADDI {first} {third} {fifth}")
        elif fourth == "-":
            if REGISTER_OPERAND.match(fifth):
                output.append(f"SUB {first} {third} {fifth}")
            else:
                if int(fifth) != 0 or first != third:
                    output.append(f"ADDI {first} {third} {-int(fifth)}")
        elif fourth == "==":
            output.append(f"CMPEQ {first} {third} {fifth}")
        elif fourth == ">":
            output.append(f"CMPLT {first} {fifth} {third}")
        elif fourth == "<":
            output.append(f"CMPLT {first} {third} {fifth}")
        elif first == "PRINT":
            output.append("NOP")
        elif first == "STORE":
            output.append(f"STORE {split[1]} {third}")
        elif third == "LOAD":
            output.append(f"LOAD {first} {fourth} {fifth if fifth else 0}")
        elif third == "CONST":
            output.append(f"LDI {first} {fourth}")
        elif len(split) == 3 and split[1] == "=":
            if first != third:
                output.append(f"MOV {first} {third}")
        elif first == "BR" and len(split) >= 6 and split[2] == "label" and split[4] == "label":
            reg = split[1][:-1] if split[1].endswith(",") else split[1]
            true_l = split[3][:-1] if split[3].endswith(",") else split[3]
            false_l = split[5][:-1] if split[5].endswith(",") else split[5]
            t_name = true_l[1:] if true_l.startswith(".") else true_l
            f_name = false_l[1:] if false_l.startswith(".") else false_l
            output.append(f"BZ {reg} {f_name}")
            output.append(f"BRA {t_name}")
        else:
            output.append("; " + line.strip())

    spilled_regs = coloring["spilled_registers"]
    color_map = dict(coloring["register_colors"])
    color_map.setdefault("s5", 5)
    color_map.setdefault("s6", 6)

    colored = []

    pseudo_reg = re.compile(r"^r(\d+|ax|sp)$|^s[56]$")
    for line in output:
        parts = []
        for word in line.split():
            base = word.rstrip(",")
            if pseudo_reg.match(base):
                if base in color_map:
                    phys = _physical_reg_number(base, color_map)
                    parts.append(f"r{phys}{word[len(base):]}")
            else:
                parts.append(word)
        colored_line = " ".join(parts)
        colored.append(colored_line)
        
    return colored
