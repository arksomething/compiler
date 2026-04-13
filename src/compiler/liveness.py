import re
import copy

REGEX_REGISTERS = re.compile(r"\b(?:[rR]\d+|rax|rsp)\b")
REGEX_NUMBER = re.compile(r"-?\d+$")

# Data RAM map (256 words): 0..99 stack (keep SP in this band if you use low memory),
# 100..127 compiler spill slots, 128..255 heap (see memory_allocator.txt).
SPILL_MEM_BASE = 100
SPILL_MEM_LIMIT = 128  # exclusive; first heap word

NAC = ("NAC", None)


def Const(n):
    return ("CONST", n)


def copy_env(env):
    return copy.copy(env)


def env_equal(a, b):
    return a == b


def join_vals(a, b):
    if a == b:
        return a
    return NAC


def join_envs(a, b):
    joined = {}
    for reg in set(a.keys()) | set(b.keys()):
        if reg in a and reg in b:
            joined[reg] = join_vals(a[reg], b[reg])
    return joined


def _const_lookup(word, env):
    if REGEX_NUMBER.fullmatch(word):
        return Const(int(word))
    return env.get(word, NAC)


def _eval_const(op, left, right):
    if left[0] != "CONST" or right[0] != "CONST":
        return NAC

    lhs = left[1]
    rhs = right[1]
    if op == "+":
        return Const(lhs + rhs)
    if op == "-":
        return Const(lhs - rhs)
    if op == "*":
        return Const(lhs * rhs)
    if op == "/":
        if rhs == 0:
            return NAC
        return Const(lhs // rhs)
    if op == "==":
        return Const(int(lhs == rhs))
    if op == "!=":
        return Const(int(lhs != rhs))
    if op == "<":
        return Const(int(lhs < rhs))
    if op == ">":
        return Const(int(lhs > rhs))
    return NAC


def _rewrite_line(line, env):
    if "=" in line:
        lhs, rhs = line.split("=", 1)
        lhs = lhs.strip()
        rhs = rhs.strip()
        split = rhs.split()

        if len(split) == 1:
            ret = _const_lookup(split[0], env)
            if ret[0] == "CONST":
                return f"{lhs} = CONST {ret[1]}"
            return line

        if len(split) == 3:
            left = _const_lookup(split[0], env)
            right = _const_lookup(split[2], env)
            ret = _eval_const(split[1], left, right)
            if ret[0] == "CONST":
                return f"{lhs} = CONST {ret[1]}"

            if (
                split[1] == "+"
                and left[0] == "CONST"
                and right[0] != "CONST"
                and REGEX_REGISTERS.fullmatch(split[2])
            ):
                return f"{lhs} = {split[2]} + {left[1]}"

            if split[1] in {"+", "-"} and right[0] == "CONST":
                return f"{lhs} = {split[0]} {split[1]} {right[1]}"

        return line

    split = re.split(r"[(),\s]+", line.strip())
    split = [part for part in split if part]
    if len(split) == 2 and split[0] == "RET":
        ret = _const_lookup(split[1], env)
        if ret[0] == "CONST":
            return f"RET {ret[1]}"
    return line


def _update_env(line, env):
    if "=" not in line:
        return

    lhs, rhs = line.split("=", 1)
    lhs = lhs.strip()
    rhs = rhs.strip()
    split = rhs.split()

    if not REGEX_REGISTERS.fullmatch(lhs):
        return

    if len(split) == 2 and split[0] == "CONST" and REGEX_NUMBER.fullmatch(split[1]):
        env[lhs] = Const(int(split[1]))
        return

    if len(split) == 1:
        ret = _const_lookup(split[0], env)
        if ret[0] == "CONST":
            env[lhs] = ret
        else:
            env[lhs] = NAC
        return

    if len(split) == 3:
        left = _const_lookup(split[0], env)
        right = _const_lookup(split[2], env)
        ret = _eval_const(split[1], left, right)
        if ret[0] == "CONST":
            env[lhs] = ret
        else:
            env[lhs] = NAC
        return

    env[lhs] = NAC


def _spill_site_kind(reg: str, line: str) -> str:
    # how reg is used
    if "=" in line:
        lhs, rhs = line.split("=", 1)
        lhs_regs = set(REGEX_REGISTERS.findall(lhs))
        rhs_regs = set(REGEX_REGISTERS.findall(rhs))
        is_def = reg in lhs_regs
        is_use = reg in rhs_regs
    else:
        is_def = False
        is_use = reg in REGEX_REGISTERS.findall(line)
    if is_def and is_use:
        return "def_and_use"
    if is_def:
        return "def"
    return "use"


class Liveness:
    def __init__(self, ir):
        self.ir = list(ir) if ir is not None else []
        self.fn_params = {}

    def analyze(self):
        self.countParams()
        self.parseNodes()
        self.cfg()
        self.constantPropagation()
        self.parseNodes()
        self.cfg()
        self.liveNodes()
        self.liveInstrs()
        self.callSaves()
        self.parseNodes()
        self.cfg()
        self.liveNodes()
        self.liveInstrs()
        self.deadCode()
        self.parseNodes()
        self.cfg()
        self.liveNodes()
        self.liveInstrs()
        self.buildInterference()
        self.coloring()
        self.spill()
        coloring = {
            "register_colors": self.register_colors,
            "spilled_registers": self.spilled_registers,
            "spill_locations": self.spill_locations,
        }
        return self.ir, coloring

    def countParams(self):
        for line in self.ir:
            split = re.split(r"[(),\s]+", line)
            if split[0] == "FUNC":
                param_names = [p for p in split[2:] if p]
                params = len(param_names)
                self.fn_params[split[1]] = params
    
    def parseNodes(self):
        blocks = []
        cur_block = []
        for i, line in enumerate(self.ir):
            if re.search(
                r"\b(JMP)|(RET)|(BR)|((r0|rax) = CALL)\b", line
            ):  
                cur_block.append(line)
                blocks.append(cur_block)
                cur_block = []
            elif re.match(r'(\.\d+:)|(FUNC)', line): # signals block start
                if cur_block:
                    blocks.append(cur_block)
                cur_block = []
                cur_block.append(line)
            else:
                cur_block.append(line)
        if cur_block:
            blocks.append(cur_block)

        self.nodes = [Node(block) for block in blocks]

    def cfg(self):
        labelToBlock = {}
        self.nodeMap = {f"b{i}":node for i, node in enumerate(self.nodes)}
        # print(self.nodeMap)
        for node in self.nodes:
            node.next = set()
            node.prev = set()
        for i, node in enumerate(self.nodes):
            if len(node.code) > 0 and re.match(r'\.\d+:', node.code[0]):
                m = re.match(r'\.\d+', node.code[0])
                if m:
                    labelToBlock[m.group(0)] = f"b{i}"

        for i, node in enumerate(self.nodes):
            for label in node.nextLabels:
                node.next.add(labelToBlock[label])

            if len(node.code) > 0 and not re.match(r"\b(JMP|RET|BR)\b", node.code[-1]):
                # must add the next one as well.
                if i != len(self.nodes) - 1:
                    node.next.add(f"b{i + 1}")

        for i, node in enumerate(self.nodes):
            for nxt in node.next:
                self.nodeMap[nxt].prev.add(f"b{i}")

    def constantPropagation(self):
        changed = True
        while changed:
            changed = False
            for node in self.nodes:
                old_in = copy_env(node.reg_in)
                old_out = copy_env(node.reg_out)
                node.calculateIn(self)
                node.recalculateOutFromIn(self)
                if not env_equal(old_in, node.reg_in) or not env_equal(old_out, node.reg_out):
                    changed = True

        new_ir = []
        for node in self.nodes:
            cur_in = copy_env(node.reg_in)
            for line in node.code:
                new_line = _rewrite_line(line, cur_in)
                new_ir.append(new_line)
                _update_env(new_line, cur_in)
        self.ir = new_ir

    def liveNodes(self):
        rev_nodes = list(reversed(self.nodes))
        changed = True
        while changed:
            changed = False
            for node in rev_nodes:
                new_out = set()
                for s in node.next:
                    new_out |= self.nodeMap[s].live_in
                
                new_in = node.uses | (new_out - node.defs)

                if new_in != node.live_in or new_out != node.live_out:
                    node.live_out = new_out
                    node.live_in = new_in
                    changed = True

    def liveInstrs(self):
        for node in self.nodes:
            instrs = node.instrs

            for i in range(len(instrs) - 1, -1, -1):
                instr = instrs[i]

                if i == len(instrs) - 1:
                    # last instruction in the block
                    instr.live_out = set(node.live_out)
                else:
                    instr.live_out = set(instrs[i + 1].live_in)

                instr.live_in = instr.uses | (instr.live_out - instr.defs)

    def callSaves(self):
        line_to_live_out = {}

        i = 0
        for node in self.nodes:
            for instr in node.instrs:
                if "CALL" in instr.code:
                    line_to_live_out[i] = instr.live_out - {"r0", "rax"}
                i += 1

        saves_before = {}
        restores_after = {}

        for call_i, regs in line_to_live_out.items():
            if not regs:
                continue

            insert_at = call_i
            for j in range(call_i - 1, -1, -1):
                line = self.ir[j]
                if "STORE" in line and "rsp" in line:
                    insert_at = j
                elif "rsp = rsp -" in line:
                    insert_at = j
                    break
                else:
                    break

            save_instrs = []
            for r in sorted(regs):
                save_instrs.append("rsp = rsp - 1")
                save_instrs.append(f"STORE {r} rsp")
            saves_before[insert_at] = save_instrs

            restore_instrs = []
            for r in sorted(regs):
                restore_instrs.append(f"{r} = LOAD rsp 0")
                restore_instrs.append("rsp = rsp + 1")
            restore_at = call_i
            if call_i + 1 < len(self.ir) and "rsp = rsp +" in self.ir[call_i + 1]:
                restore_at = call_i + 1
            restores_after[restore_at] = restore_instrs

        new_ir = []
        for j, line in enumerate(self.ir):
            if j in saves_before:
                new_ir.extend(saves_before[j])
            new_ir.append(line)
            if j in restores_after:
                new_ir.extend(restores_after[j])
        self.ir = new_ir

    def deadCode(self):
        deadLines = set()
        i = 0
        for node in self.nodes:
            for instr in node.instrs:
                if re.match(r"^(?!.*\bCALL\b)r\d+\s*=", instr.code):
                    if instr.code.split(" ")[0] not in instr.live_out:
                        deadLines.add(i)
                i += 1 
        new_ir = []
        for i, line in enumerate(self.ir):
            if i not in deadLines:
                new_ir.append(line)

        self.ir = new_ir

    def buildInterference(self):
        self.interferenceGraph = {}

        for node in self.nodes:
            for instr in node.instrs:
                m = re.match(r"^(rax|r\d+|rsp)\b", instr.code)
                if m:
                    reg = m.group(1)
                    if reg not in self.interferenceGraph:
                        self.interferenceGraph[reg] = set()

                    for out in instr.live_out:
                        if out == reg:
                            continue

                        if out not in self.interferenceGraph:
                            self.interferenceGraph[out] = set()

                        self.interferenceGraph[reg].add(out)
                        self.interferenceGraph[out].add(reg)

    def coloring(self):
        k = 4
        working_graph = copy.deepcopy(self.interferenceGraph)
        working_keys = set(working_graph.keys())
        s = []
        while working_keys:
            m = None
            keys_snapshot = list(working_keys)
            for i, key in enumerate(keys_snapshot):
                if key not in working_graph:
                    continue
                if len(working_graph[key]) < k:
                    for cur in list(working_keys):
                        if cur != key:
                            working_graph[cur].discard(key)
                    working_keys.remove(key)
                    del working_graph[key]
                    s.append((key, False))
                    break
                m_deg = len(working_graph[m]) if m is not None else -1
                if len(working_graph[key]) > m_deg:
                    m = key
                if i == len(keys_snapshot) - 1:
                    for cur in list(working_keys):
                        if cur != m:
                            working_graph[cur].discard(m)
                    working_keys.remove(m)
                    del working_graph[m]
                    s.append((m, True))
        
        colors = {}
        spilled = set()
        while s:
            reg, _removed_as_spill = s.pop()
            adjs = self.interferenceGraph.get(reg, set())
            available = set(range(k))
            for adj in adjs:
                if adj in colors:
                    available.discard(colors[adj])
            if not available:
                spilled.add(reg)
            else:
                colors[reg] = next(iter(available))

        spilled -= {"rax", "rsp"}
        colors["rax"] = 0
        colors["rsp"] = 7
        self.register_colors = colors
        self.spilled_registers = list(spilled)

    def spill(self):
        spilled = set(self.spilled_registers)
        spill_i = {r:i for i, r in enumerate(spilled)}
        self.spill_locations = {reg: [] for reg in spilled}
        loads_before = {}
        stores_after = {}
        for i, line in enumerate(self.ir):
            mentioned = set(REGEX_REGISTERS.findall(line))
            for reg in mentioned & spilled:
                if reg in ("rax", "rsp"):
                    continue
                kind = _spill_site_kind(reg, line)
                self.spill_locations[reg].append((i, line, kind))
                addr = SPILL_MEM_BASE + spill_i[reg]
                if addr >= SPILL_MEM_LIMIT:
                    raise ValueError(
                        f"spill address {addr} for {reg} must stay < {SPILL_MEM_LIMIT} (heap starts at {SPILL_MEM_LIMIT})"
                    )
                if kind in ("use", "def_and_use"):
                    loads_before.setdefault(i, []).append(f"s5 = CONST {addr}")
                    loads_before.setdefault(i, []).append(f"s6 = LOAD s5 0")
                    loads_before.setdefault(i, []).append(f"s5 = CONST 0")
                if kind in ("def", "def_and_use"):
                    stores_after.setdefault(i, []).append(f"s5 = CONST {addr}")
                    stores_after.setdefault(i, []).append(f"STORE s6 s5")
                    stores_after.setdefault(i, []).append(f"s5 = CONST 0")

        snapshot = list(self.ir)
        new_ir = []
        for j, line in enumerate(snapshot):
            modified = line
            mentioned = set(REGEX_REGISTERS.findall(line))
            for reg in sorted(mentioned & spilled):
                modified = re.sub(rf"\b{re.escape(reg)}\b", "s6", modified)
            for pseudo in loads_before.get(j, []):
                new_ir.append(pseudo)
            new_ir.append(modified)
            for pseudo in stores_after.get(j, []):
                new_ir.append(pseudo)
        self.ir[:] = new_ir

class Node:
    def __init__(self, code):
        self.code = code # arr of strings - the ir
        self.defs = set() # def
        self.uses = set() # use
        self.nextLabels = set()
        self.next = set()
        self.prev = set()
        self.live_in = set()
        self.live_out = set()
        self.reg_in = {}
        self.reg_out = {}
        self.calculateLiveness(code)

    def calculateLiveness(self, code):
        self.code = code
        self.defs = set()
        self.uses = set()
        self.nextLabels = set()
        self.next = set()
        self.prev = set()
        self.live_in = set()
        self.live_out = set()
        self.instrs = [Instr(line) for line in code]
        for i, line in enumerate(code):
            if len(line.split("=")) == 2:
                lhs, rhs = line.split("=", 1)
                self.defs.update(REGEX_REGISTERS.findall(lhs))

                for reg in REGEX_REGISTERS.findall(rhs):
                    if reg not in self.defs:
                        self.uses.add(reg)

            elif len(line.split("=")) == 1:
                for reg in REGEX_REGISTERS.findall(line):
                    if reg not in self.defs:
                        self.uses.add(reg)

            if i == len(code) - 1:
                if re.search(r"\b(JMP|RET|BR)\b", line):
                    self.nextLabels = set(re.findall(r"\.\d+", line))

    def calculateIn(self, liveness):
        if not self.prev:
            self.reg_in = {}
            return

        regs = None
        for prev in self.prev:
            prev_out = liveness.nodeMap[prev].reg_out
            if regs is None:
                regs = copy_env(prev_out)
            else:
                regs = join_envs(regs, prev_out)
        self.reg_in = regs if regs is not None else {}

    def recalculateOutFromIn(self, liveness):
        regs = copy_env(self.reg_in)
        for line in self.code:
            _update_env(line, regs)
        self.reg_out = regs

    def __repr__(self):
        head = self.code[0] if self.code else "?"
        # return f"Node({head!r} defs={self.defs} uses={self.uses} next={list(self.next)})"
        return f"Node({head!r} in={self.live_in} out={self.live_out} next={list(self.next)})"

class Instr:
    def __init__(self, code):
        self.code = code
        self.defs = set()
        self.uses = set()
        self.live_in = set()
        self.live_out = set()

        if "=" in code:
            lhs, rhs = code.split("=", 1)
            self.defs.update(REGEX_REGISTERS.findall(lhs))
            for reg in REGEX_REGISTERS.findall(rhs):
                if reg not in self.defs:
                    self.uses.add(reg)
        else:
            for reg in REGEX_REGISTERS.findall(code):
                self.uses.add(reg)

    def __repr__(self):
        return f"Instr({self.code!r}, in={self.live_in}, out={self.live_out})"
            
