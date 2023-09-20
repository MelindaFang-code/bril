import json
import sys
from collections import defaultdict, OrderedDict
from utils import get_blocks
from cfg import cfg, nameToBlock, append_terminator

dominance_utilities = ['dominators', 'tree', 'frontier']

def postOrder(name2Block, successors, entry, seen, order):
    seen.add(entry)
    for p in successors[entry]:
        if p not in seen:
            postOrder(name2Block, successors, p, seen, order)
    order.append(entry)
    return

#example use: map from block to its dominators
def reverse_map(dom):
    reverse = defaultdict(set)
    for b, doms in dom.items():
        for d in doms:
            reverse[d].add(b)
    return reverse
            
def getEntry(name2block, predecessors):
    for n in name2block:
        if len(predecessors[n]) == 0:
            return n

def findStrict(dom):
    strict = dom.copy()
    for d, bs in dom.items():
        strict[d].remove(d)
        
# map from block to its dominators
def dominators(name2block, predecessors, successors):
    entry = getEntry(name2block, predecessors)
    dom = OrderedDict()
    dom[entry] = set([entry])
    changing = True
    blockNames = []
    postOrder(name2block, successors, entry, set(), blockNames)
    #get reversed post order 
    blockNames=list(reversed(blockNames))
    # now dom are ordered by reverse post order
    for n in blockNames[1:]:
        dom[n] = set(name2block.keys())
    changes = 1
    while changes != 0:
        changes = 0
        for vertex in blockNames:
            if vertex == entry:
                continue
            preds = set(blockNames)
            for p in predecessors[vertex]:
                preds = preds.intersection(dom[p])
            preds.add(vertex)
            if preds != dom[vertex]:
                changes += 1
                dom[vertex] = preds
    return dom

#dominance frontier of a node d is the set of all nodes ni 
#such that d dominates an immediate predecessor of ni, 
#but d does not strictly dominate ni 
#It is the set of nodes where d's dominance stops.
def dominance_frontier(dom, predecessors, successors):
    frontiers = {}
    # get map from block to the block's dominators
    rev_dom = reverse_map(dom)
    # print(rev_dom)
    for b in dom:
        dom_children = set()
        # for children of blocks dominated by b
        for d in rev_dom[b]:
            dom_children.update(successors[d])
        frontiers[b] = [c for c in dom_children if c not in rev_dom[b] or c == b]
    return frontiers

# node A is node B's parent if A strictly dominates B
# A dominates B and A doesn't strictly dominate B's strictly dominators
# map from block to its children in tree
def dominance_tree(dom):
    tree = {}
    rev_dom = reverse_map(dom)
    for b in dom:
        tree[b] = rev_dom[b].copy()
        tree[b].remove(b)
        # print(b, tree[b])
        for d in rev_dom[b]:
            for strict_dom in dom[d]:
                if strict_dom == d or strict_dom not in tree[b]:
                    # print(d, strict_dom)
                    continue
                elif d in tree[b]:
                    tree[b].remove(d)
        # print(b, tree[b])
    return tree

def run(functions, domType):
    for func in functions['functions']:
        instructions = func['instrs']
        workList = get_blocks(instructions)
        name2block = nameToBlock(workList)
        append_terminator(name2block)
        predecessors, successors = cfg(name2block)
        dom = dominators(name2block, predecessors, successors)
        if domType == "dominators":
            print("dom", dom)
        elif domType == "frontier":
            front = dominance_frontier(dom, predecessors, successors)
            print("frontier", front)
        elif domType == "tree":
            tree = dominance_tree(dom)
            print("dom_tree", tree)
        
#bril2json < ../examples/test/df/cond.bril | python3 dominance.py dominators
#bril2json < ../examples/test/dom/loopcond.bril | python3 dominance.py dominators
#bril2json < ../examples/test/dom/loopcond.bril | python3 dominance.py tree
#bril2json < ../examples/test/dom/loopcond.bril | python3 dominance.py frontier

if __name__ == "__main__":
    f = json.load(sys.stdin)
    d = sys.argv[1]
    if d not in dominance_utilities:
        print("unsupported dominance utilities")
    else:
        run(f, d)