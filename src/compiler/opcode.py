for i, line in enumerate(ir):
        if not line:
            continue

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
            fname = split[1]
            param_names = [p for p in split[2:] if p]
            params = len(param_names)
            output.append("." + split[1])
            search_start = i + 1
            for param in range(params):
                arg_reg = "a" + str(arg_n)
                arg_n += 1
                func_regs[fname].append(arg_reg)
                cur_line_i = search_start
                toWrite = True
                while toWrite and cur_line_i < len(ir):
                    cur_line = ir[cur_line_i]
                    cur_split = re.split(r"[(),\s]+", cur_line)
                    if (
                        len(cur_split) >= 4
                        and cur_split[1] == "="
                        and cur_split[2] == "ARG"
                        and cur_split[3] == str(param)
                    ):
                        ir[cur_line_i] = cur_split[0] + " = " + arg_reg
                        search_start = cur_line_i + 1
                        toWrite = False
                    else:
                        cur_line_i += 1
        elif first == "RET":
            if len(split) > 1 and split[1]:
                output.append(f"MOV rax {split[1]}")
            output.append("RET")
        elif first == "JMP":
            output.append(f"JMP {third}")
        elif third == "CALL":
            callee = fourth
            params_call = [t for t in split[4:] if t]
            for j, param in enumerate(params_call):
                if j < len(func_regs[callee]):
                    a_reg = func_regs[callee][j]
                    output.append(f"MOV {a_reg} {param}")
            output.append("CALL " + callee)
            output.append(f"MOV {first} rax")
        elif fourth == "+":
            output.append(f"ADD {first} {third} {fifth}")
        elif fourth == "-":
            output.append(f"SUB {first} {third} {fifth}")
        elif fourt