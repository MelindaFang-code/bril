import json
import sys
from collections import defaultdict
from utils import get_blocks
from cfg import cfg, nameToBlock, append_terminator

dfs = ['live', 'cpp', 'defined']
def union(set_list):
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

def live_transfer(block, out_set):
    uses = getUses(block)
    defs = getDefs(block)
    uses.update(out_set-defs)
    return uses

def defined_transfer(block, out_set):
    defs = getDefs(block)
    out = out_set.copy()
    out.update(defs)
    return out

def dataFlow(name2block, merge, transfer, isBack):
    predecessors, successors = cfg(name2block)
    workList = list(name2block.items())
    if not isBack:
        predecessors, successors = successors, predecessors
        workList = list(reversed(workList))
    
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
            for p in predecessors[b]:
                workList.append((p, name2block[p]))
    return inMap, outMap

def run(functions, dfType):
    for func in functions['functions']:
        instructions = func['instrs']
        workList = get_blocks(instructions)
        name2block = nameToBlock(workList)
        append_terminator(name2block)
        
        if dfType == "live":
            merge = union
            transfer = live_transfer
            isBack = True
        elif dfType == "defined":
            merge = union
            transfer = defined_transfer
            isBack = False
        
        inmap, outmap = dataFlow(name2block, merge, transfer, isBack)
        if not isBack:
            inmap, outmap = outmap, inmap
        print("in", inmap)
        print("out", outmap)

if __name__ == "__main__":
    f = json.load(sys.stdin)
    dfType = sys.argv[1]
    if dfType not in dfs:
        print("unsupported dataflow type")
    else:
        run(f, dfType)
