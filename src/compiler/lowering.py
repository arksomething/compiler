"""Expand FUNC/ARG/CALL/RET, then run the same register passes as ``generation.py``."""

import copy
import re
from collections import defaultdict


def _split_token(word):
    """``r2,`` -> (``r2``, ``,``) for int parsing; inner word has no trailing comma."""
    w = word.rstrip(",")
    return w, word[len(w) :]


def lower_ir(ir):
    """Return a new instruction list; ``ir`` is not mutated (ARG lines are rewritten on a copy)."""
    ir = copy.copy(ir)
    func_regs = defaultdict(list)
    arg_n = 0
    output = []

    for i, line in enumerate(ir):
        if not line:
            continue

        split = re.split(r"[()\s]+", line)
        first = split[0]
        if not first:
            continue
        third = split[2] if len(split) > 2 else None
        fourth = split[3] if len(split) > 3 else None

        if first[0] == ".":
            output.append(line.strip())
        elif first == "FUNC":
            fname = split[1]
            param_names = [p for p in split[2:] if p]
            params = len(param_names)
            output.append(f"FUNC {fname} ({', '.join(param_names)})")
            search_start = i + 1
            for param in range(params):
                arg_reg = "a" + str(arg_n)
                arg_n += 1
                func_regs[fname].append(arg_reg)
                cur_line_i = search_start
                to_write = True
                while to_write and cur_line_i < len(ir):
                    cur_line = ir[cur_line_i]
                    cur_split = re.split(r"[()\s]+", cur_line)
                    if (
                        len(cur_split) >= 4
                        and cur_split[1] == "="
                        and cur_split[2] == "ARG"
                        and cur_split[3] == str(param)
                    ):
                        ir[cur_line_i] = cur_split[0] + " = " + arg_reg
                        search_start = cur_line_i + 1
                        to_write = False
                    else:
                        cur_line_i += 1
        elif first == "RET":
            if len(split) > 1 and split[1]:
                output.append(f"rax = {split[1]}")
            output.append("RET")
        elif third == "CALL":
            callee = fourth
            params_call = [t for t in split[4:] if t]
            for j, param in enumerate(params_call):
                if j < len(func_regs[callee]):
                    a_reg = func_regs[callee][j]
                    output.append(f"{a_reg} = {param}")
            output.append("CALL " + callee)
            output.append(f"{first} = rax")
        else:
            output.append(line.strip())

    second_pass = []
    biggest = 0
    for line in output:
        cur_line = []
        for word in line.split():
            w, suf = _split_token(word)
            if w and w[0] == "r":
                if len(w) > 1 and w[1] == "a":
                    cur_line.append("r0" + suf)
                else:
                    biggest = max(int(w[1:]) + 1, biggest)
                    cur_line.append(f"r{int(w[1:]) + 1}" + suf)
            else:
                cur_line.append(word)
        second_pass.append(" ".join(cur_line))

    third_pass = []
    for line in second_pass:
        cur_line = []
        for word in line.split():
            w, suf = _split_token(word)
            if w and w[0] == "a":
                cur_line.append(f"r{biggest + int(w[1:]) + 1}" + suf)
            else:
                cur_line.append(word)
        third_pass.append(" ".join(cur_line))
    return third_pass
