import json
import sys
from collections import defaultdict
from utils import get_blocks
from cfg import cfg, nameToBlock, append_terminator

def merge(set_list):
    cur_set = set()
    for s in set_list:
        cur_set.update(s)
    return cur_set

def getDefs(block):
    defs = set()
    for b in block:
        if "dest" in b:
            defs.add(b['dest'])
    return defs

def getUses(block):
    uses = set()
    defs = set()
    for b in block:
        if "args" in b:
            for a in b['args']:
                if a not in defs:
                    uses.add(a)
        if 'dest' in b:
            defs.add(b['dest'])
    return uses

def transfer(block, out_set):
    uses = getUses(block)
    defs = getDefs(block)
    print('out', out_set)
    print('use', uses)
    print('defs', defs)
    uses.update(out_set-defs)
    return uses


def dataFlow(name2block):
    predecessors, successors = cfg(name2block)
    print('pred', predecessors)
    print('suc', successors)
    workList = list(name2block.items())

    inMap = {name: set() for name in name2block}
    outMap = {name: set() for name in name2block}

    while len(workList) > 0:
        b, block = workList.pop(0)
        outMap[b] = merge(inMap[p] for p in successors[b])
        newIn = transfer(block, outMap[b])
        if newIn == inMap[b]:
            continue
        else:
            inMap[b] = newIn
            workList.append((b, block))
    return inMap, outMap

def run(functions):
    for func in functions['functions']:
        instructions = func['instrs']
        workList = get_blocks(instructions)
        name2block = nameToBlock(workList)
        append_terminator(name2block)
        inmap, outmap = dataFlow(name2block)
        print("in", inmap)
        print("out", outmap)

if __name__ == "__main__":
    f = json.load(sys.stdin)
    run(f)
    # json.dump(f, sys.stdout, indent=2, sort_keys=True)