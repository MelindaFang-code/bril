import json
import sys
from collections import defaultdict

terminators = ['br', 'jmp', 'ret']
ops = {
    'add': lambda a, b: a + b,
    'mul': lambda a, b: a * b,
    'sub': lambda a, b: a - b,
    'div': lambda a, b: a // b,
}
#ins: ('add', (0,1))
def calc(ops, ins, table):
    if ins[0] in ops:
        try:
            a = table[ins[1][0]][0][1]
            b = table[ins[1][1]][0][1]
            # print(a,b,ops[ins[0]](a,b))
            return ops[ins[0]](a,b)
        except: 
            return None
    else:
        return None
#return list of blocks
def get_blocks(instr):
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
        # print(used)
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
                seen.add(i['dest'])
                if i['dest'] in alive:
                    alive.remove(i['dest'])
        if i.get("args"):
            alive.update(i['args']) 
            # print(alive) 
            for a in i['args']:
                if a in seen:
                    seen.remove(a)
        itr -= 1
    return changed

def find_last_def(instr):
    last_def = {}
    for i in range(len(instr)-1,-1,-1):
        if 'dest' not in instr[i] or instr[i]['dest'] in last_def:
            continue
        else:
            last_def[instr[i]['dest']] = i
    return last_def

def local_value_numbering(instr):
    #[value, var]
    table = []
    #var to table row
    var2num = dict()
    #val to table row
    tableMapping = dict()
    last_def = find_last_def(instr)
    for i, inst in enumerate(instr):
        # print(inst)
        # val = ()
        skip = False
        if 'op' in inst and inst['op'] == 'const':
            val = (inst["op"], inst['value'])
        elif 'op' in inst and (inst['op'] in terminators or inst['op'] == 'call'):
            skip = True
        elif 'args' in inst:
            lst = []
            for a in inst['args']:
                if a not in var2num:
                    skip = True
                    break               
                else:
                    lst.append(var2num[a])
            lst.sort()
            val = (inst["op"], tuple(lst))
        else:
            skip = True
        # print(tableMapping, table, var2num, inst)
        if not skip:
            # print(val)
            if 'dest' in inst:
                dest = inst["dest"]
            else:
                dest = None
            if val in tableMapping:
                num = tableMapping[val]
                _ , var = table[num]
                if inst['op'] != 'const':
                    inst['args'] = [var]
                    inst['op'] = 'id'
            elif inst["op"] == 'id' and inst['args'][0] in var2num:
                num = var2num[inst['args'][0]]
                inst['args'] = [table[num][1]]
                # print('op',inst)
            else:
                num = len(table)
                const = calc(ops, val, table)
                
                if dest:
                    if last_def[dest] < i:
                        dest = dest+str(uuid())
                        inst['dest'] = dest
                # x = a + b ... x = 5 .. y = a+b (can't write y = id x)
                # x'= a+b ... x = 5 ... y = x'
                    tableMapping[val] = num
                    table.append([val, dest])
                if 'args' in inst:
                    for i, a in enumerate(inst['args']):
                        inst['args'][i] = table[var2num[a]][1]
                if const is not None:
                    inst['op'] = 'const'
                    inst['value'] = const
                    del inst['args']
            
            if dest:
                var2num[dest] = num
		

def iterate(program):
    run = True
    while run:
        run = trivial_dce(program['instrs'])
    blocks = get_blocks(program['instrs'])
    program['instrs'] = []
    for i, b in enumerate(blocks):
        local_value_numbering(b)
        while run:
            run = local_opt(b)
        program['instrs'] += b
        run = True
    while run:
        run = trivial_dce(program['instrs'])

#examples/test/tdce/simple.bril
if __name__ == "__main__":
    f = json.load(sys.stdin)
    for func in f['functions']:
        iterate(func)
        # print("func", func['instrs'])

    # print("bril", bril['functions'])
    json.dump(f, sys.stdout, indent=2, sort_keys=True)


