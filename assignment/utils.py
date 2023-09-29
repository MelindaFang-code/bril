

terminators = ['br', 'jmp', 'ret']

ops = {
    'add': lambda a, b: a + b,
    'mul': lambda a, b: a * b,
    'sub': lambda a, b: a - b,
    'div': lambda a, b: a // b,
}

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

def get_defs(block):
    defs = set()
    for b in block:
        if "dest" in b:
            defs.add(b['dest'])
    return defs
