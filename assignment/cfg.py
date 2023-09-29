from collections import OrderedDict, defaultdict
from utils import terminators

#create name2block map in reversed order
def nameToBlock(block_list):
    name2block = OrderedDict()
    idx = len(block_list)-1
    for b in reversed(block_list):
        if 'label' in b[0]:
            name = b[0]['label']
            b = b[1:]
        else:
            name = "b"+str(idx)
        name2block[name] = b
        idx -= 1
    return name2block

#ensure entry has no predecessor
def add_entry(block_map, preds, succs):
    lb = list(block_map.keys())[-1]
    if len(preds[lb]) == 0:
        return
    e = 'entry1'
    block_map[e] = []
    preds[e] = set()
    succs[e] = set([lb])
    return 

#traverse through the reversed ordered dict
#keep track of the "next" label
def append_terminator(block_map):
    nxt = ''
    for i,(name, b) in enumerate(block_map.items()):
        #dummy block added at the end/front
        if len(b) == 0 or 'op' not in b[-1] or b[-1]['op'] not in terminators:
            if i == 0:
                b.append({'op':'ret', "args": []})
            else:
                b.append({'op':'jmp', "labels": [nxt]})
        nxt = name

#return the predecessor and successors
def cfg(block_map):
    predecessors = {name: set() for name in block_map}
    successors = {name: set() for name in block_map}
    for name, block in block_map.items():
        ins = block[-1]
        if ins.get('op') and ins['op'] in ('jmp', 'br'):
            for l in ins['labels']:
                successors[name].add(l)
                predecessors[l].add(name)
    return predecessors, successors

def get_defs_map(block_map):
    defs = defaultdict(set)
    for name, b in block_map.items():
        for ins in b:
            if "dest" in ins:
                defs[(ins['dest'], ins['type'])].add(name)
    return defs
    