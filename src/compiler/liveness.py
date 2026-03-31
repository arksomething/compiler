import re
import copy

REGEX_REGISTERS = re.compile(r'\b[rR]\d+\b')


def _spill_site_kind(reg: str, line: str) -> str:
    """Whether ``reg`` is defined and/or used on this IR line."""
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

    def analyze(self):
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
    
    def parseNodes(self):
        blocks = []
        cur_block = []
        for i, line in enumerate(self.ir):
            if re.search(r'\b(JMP)|(RET)|(BR)\b', line):
                cur_block.append(line)
                blocks.append(cur_block)
                cur_block = []
            elif re.match(r'(\.\d+:)|(FUNC)', line):
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
        
    def buildInterference(self):
        self.interferenceGraph = {}

        for node in self.nodes:
            for instr in node.instrs:
                if re.match(r"r\d+\b", instr.code):
                    reg = instr.code.split()[0]
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
        k = 2
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

        self.register_colors = colors
        self.spilled_registers = spilled

    def spill(self):
        spilled = self.spilled_registers
        self.spill_locations = {reg: [] for reg in spilled}
        loads_before = {}
        stores_after = {}
        for i, line in enumerate(self.ir):
            mentioned = set(REGEX_REGISTERS.findall(line))
            for reg in mentioned & spilled:
                kind = _spill_site_kind(reg, line)
                self.spill_locations[reg].append((i, line, kind))
                if kind in ("use", "def_and_use"):
                    loads_before.setdefault(i, []).append(f"SPILL_LOAD {reg}")
                if kind in ("def", "def_and_use"):
                    stores_after.setdefault(i, []).append(f"SPILL_STORE {reg}")

        snapshot = list(self.ir)
        new_ir = []
        for j, line in enumerate(snapshot):
            for pseudo in loads_before.get(j, []):
                new_ir.append(pseudo)
            new_ir.append(line)
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
            
