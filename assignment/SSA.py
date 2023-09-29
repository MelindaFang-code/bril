# One thing to watch out for: variables that are undefined along some paths.
# if you want to check the midpoint of that round trip.
# bonus: implement global value numbering for SSA-form Bril code.
from dominance import dominance_frontier
import json
import sys
from collections import defaultdict, OrderedDict
from utils import get_blocks, get_defs
from cfg import cfg, nameToBlock, get_defs_map, append_terminator, add_entry
from dominance import dominators, dominance_frontier, dominance_tree, getEntry

#return map from block name to phi_node map {var: [[label list][arg list]]}
def insertNodes(var2defBlock, dom, predecessors, successors):
    df = dominance_frontier(dom, predecessors, successors)
    phis = {}
    for v, def_blocks in var2defBlock.items():
        var, varType = v[0], v[1]
        def_blocks_list=list(def_blocks)
        for d in def_blocks_list:
            for b in df[d]:  # for b in dom frontier of d st v is defined
                #Add a ϕ-node to block, if not done previously
                if b not in phis:
                    phis[b] = {}
                if v not in phis[b]:
                    phis[b][var] = {
                        'op': 'phi',
                        'labels': [],
                        'args': [],
                        'type': varType
                    }
                #add b to the defBlock of v because it now writes to v
                if b not in def_blocks_list: 
                    def_blocks_list.append(b)
    return phis

def new_name(counter, old_name, stack):
    new = old_name + "." + str(counter[old_name])
    counter[old_name] += 1
    stack[old_name].append(new)
    return new

#stack[v] is a stack of variable names (for every variable v)
#block: block name, counter: {old_name: rename counts}
def rename(block, stack, counter, name2block, successors, phis, dom_tree):

    pushed_vars = {k: len(v) for k, v in stack.items()}

    if block in phis:
        for v,p in phis[block].items():
            p['dest'] = new_name(counter, v, stack)

    for instr in name2block[block]:
        #replace each argument to instr with stack[old name]
        if "args" in instr:
            instr['args'] = [stack[old][-1] for old in instr['args']]
        #replace instr's destination with a new name
        #push that new name onto stack[old name]
        if "dest" in instr:
            instr['dest'] = new_name(counter, instr["dest"], stack)

    for s in successors[block]:
        if s in phis:
            for v in phis[s]:
                if v not in stack:
                    phis[s].pop(v)
                else:
                    phis[s][v]['labels'].append(block)
                    phis[s][v]['args'].append(stack[v][-1])
                
    if block in dom_tree:
        for b in dom_tree[block]:
            rename(b, stack, counter, name2block, successors, phis, dom_tree)
       
    #pop all the names we just pushed onto the stacks
    for var in stack:
        if var in pushed_vars:
            prev_vars_cnt = pushed_vars[var]
            stack[var] = stack[var][:prev_vars_cnt]

#phis[block][v] = [renamed vs] args
def add_phi_instr(name2block, phis):
    new_instrs = []
    for name, instrs in reversed(name2block.items()):
        new_instrs.append({'label': name})
        if name in phis:
            for dest, phi in sorted(phis[name].items()):
                if len(phi['labels']) > 1:
                    new_instrs.append(phi)
        new_instrs += instrs
    return new_instrs

def to_ssa(functions):
    for func in functions['functions']:
        instructions = func['instrs']
        workList = get_blocks(instructions)
        name2block = nameToBlock(workList)
        append_terminator(name2block)
        predecessors, successors = cfg(name2block)
        add_entry(name2block, predecessors, successors)
        dom = dominators(name2block, predecessors, successors)
        dom_tree = dominance_tree(dom)
        var2defBlock = get_defs_map(name2block)
        counter = {}
        stack = {}
        if "args" in func:
            for a in func['args']:
                stack[a['name']] = [a['name']]
        for v in var2defBlock.keys():
            varName, varType = v[0], v[1]
            stack[varName] = [varName]
            counter[varName] = 0

        phi_nodes = insertNodes(var2defBlock, dom, predecessors, successors)
        entry = getEntry(name2block, predecessors)
        rename(entry, stack, counter, name2block, successors, phi_nodes, dom_tree)
        func['instrs'] = add_phi_instr(name2block, phi_nodes)


def func_ssa(func):
    workList = get_blocks(func['instrs'])
    name2block = nameToBlock(workList)
    predecessors, successors = cfg(name2block)
    add_entry(name2block, predecessors, successors)
    # Replace each phi-node.
    for name, instrs in name2block.items():
        # Insert copies for each phi.
        for instr in instrs:
            if instr.get('op') == 'phi':
                dest = instr['dest']
                t = instr['type']
                for var, label in zip(instr['args'], instr['labels']):
                    name2block[label].insert(-1, {
                        'op': 'id',
                        'type': t,
                        'args': [var],
                        'dest': dest,
                    })

        # Remove all phis.
        new_block = [i for i in instrs if i.get('op') != 'phi']
        instrs[:] = new_block

    new_instrs = []
    for name, instrs in reversed(name2block.items()):
        new_instrs += instrs
    func['instrs'] = new_instrs

#1. insert code into the `phi`-containing block’s **immediate predecessors** along paths: 
    #1. one that does `v = id x` 
    #2. one that does `v = id y`. 
#2. delete the `phi` instruction.
def from_ssa(functions):
    for func in functions['functions']:
        func_ssa(func)

# check programs do the same thing when converted to SSA form and back again.
# output of your “to SSA” pass is actually in SSA form: is_ssa.py script
def test():
    return True

#bril2json < ../examples/test/to_ssa/loop.bril | python3 SSA.py
if __name__ == "__main__":
    f = json.load(sys.stdin)
    to_ssa(f)
    # from_ssa(f)
    print(json.dumps(f, indent=2, sort_keys=True))
