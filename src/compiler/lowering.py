import copy
import re
from collections import defaultdict

ARG_REGISTER = re.compile(r"^a\d+$")
PSEUDO_REGISTER = re.compile(r"^r\d+$")

def _split_token(word):
    w = word.rstrip(",")
    return w, word[len(w) :]


def lower_ir(ir):
    ir = copy.copy(ir)
    func_regs = defaultdict(list)
    arg_n = 0
    output = []

    for i, line in enumerate(ir):
        if not line:
            continue

        split = re.split(r"[(),\s]+", line)
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
                    cur_split = re.split(r"[(),\s]+", cur_line)
                    if (
                        len(cur_split) >= 4
                        and cur_split[1] == "="
                        and cur_split[2] == "ARG"
                        and cur_split[3] == str(param)
                    ):
                        # ir[cur_line_i] = cur_split[0] + " = " + arg_reg
                        ir[cur_line_i] = f"{cur_split[0]} = LOAD rsp {param + 1}"
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
            for j in range(len(params_call) - 1, -1, -1):
                output.append("rsp = rsp - 1")
                output.append(f"STORE {params_call[j]} rsp")
            output.append("rax = CALL " + callee)
            if params_call:
                output.append(f"rsp = rsp + {len(params_call)}")
            output.append(f"{first} = rax")
        else:
            output.append(line.strip())

    second_pass = []
    biggest = 0
    for line in output:
        cur_line = []
        for word in line.split():
            w, suf = _split_token(word)
            if w == "rax":
                cur_line.append("r0" + suf)
            elif PSEUDO_REGISTER.match(w):
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
            if ARG_REGISTER.match(w):
                cur_line.append(f"r{biggest + int(w[1:]) + 1}" + suf)
            else:
                cur_line.append(word)
        third_pass.append(" ".join(cur_line))
    return third_pass
