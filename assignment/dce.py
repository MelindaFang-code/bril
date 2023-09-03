import json
import sys
from collections import defaultdict

#return list of blocks
def get_blocks(instr):
    terminators = ['br', 'jmp', 'ret']
    cur_block = []
    out = []
    for i in instr:
        if i.get('op'):  
            cur_block.append(i)
            if i['op'] in terminators:
                out.append(cur_block)
                cur_block = []
        #label
        else:  
            if cur_block:
                out.append(cur_block)
            cur_block = [i]
    if cur_block:
        out.append(cur_block)
    return out

def trivial_dce(instr):
    changed = False
    used = set()
    for i in instr:
        if i.get("args"):
            used.update(i['args'])
    
    itr = 0
    keep_ptr = 0
    while itr < len(instr):
        i = instr[itr]
        if i.get("dest") and i['dest'] not in used:
            changed = True
            del instr[itr]
        else:
            itr += 1
    return changed
            
def local_opt(instr):
    alive = set()
    seen = set()
    changed = False
    itr = len(instr) - 1
    while itr >= 0:
        i = instr[itr]
        if i.get("dest"):
            if i['dest'] not in alive and i['dest'] in seen:
                # print(i, itr)
                del instr[itr]
                changed = True   
            else:
                print(i, itr)
                seen.add(i['dest'])
                alive.remove(i['dest'])
        if i.get("args"):
            alive.update(i['args']) 
            # print(alive) 
            for a in i['args']:
                if a in seen:
                    seen.remove(a)
        itr -= 1
    return changed

def iterate(program):
    run = True
    while run:
        run = trivial_dce(program['instrs'])
    blocks = get_blocks(program['instrs'])
    program['instrs'] = []
    for i, b in enumerate(blocks):
        # print(i, b)
        while run:
            run = local_opt(b)
        program['instrs'] += b
        run = True

#examples/test/tdce/simple.bril
if __name__ == "__main__":
    f = json.load(sys.stdin)
    for func in f['functions']:
        iterate(func)
        # print("func", func['instrs'])

    # print("bril", bril['functions'])
    json.dump(f, sys.stdout, indent=2, sort_keys=True)


