import z3
import lark

#only gives one answer
def solve(phi):
    s = z3.Solver()
    s.add(phi)
    s.check()
    return s.model()

def examples():
    formula = (z3.Int('x') / 7 == 6)
    print(solve(formula))
    y = z3.BitVec('y', 8)
    # y = 5, shifted by 3 equals 40
    print(solve(y << 3 == 40))
    z = z3.Int('z')
    n = z3.Int('n')
    print(solve(z3.ForAll([z], z * n == z)))

def sketching():
    x = z3.BitVec('x', 8)
    slow_expr = x * 2
    h = z3.BitVec('h', 8)  # The hole, a.k.a. ??
    fast_expr = x << h
    goal = z3.ForAll([x], slow_expr == fast_expr)
    print(solve(goal))

GRAMMAR = """
?start: sum
    | sum "?" sum ":" sum -> if

?sum: term
    | sum "+" term        -> add
    | sum "-" term        -> sub

?term: item
    | term "*"  item      -> mul
    | term "/"  item      -> div
    | term ">>" item      -> shr
    | term "<<" item      -> shl

?array: "[" start ("," start)* "]"

?item: NUMBER           -> num
    | "-" item          -> neg
    | CNAME             -> var
    | "(" start ")"
    | array             -> arr
    | "get" item array -> get

%import common.CNAME
%import common.NUMBER
%ignore " "
""".strip()

#take in a function to lookup variables
def interp(tree, lookup):
    op = tree.data
    if op in ('add', 'sub', 'mul', 'div', 'shl', 'shr'):
        lhs = interp(tree.children[0], lookup)
        rhs = interp(tree.children[1], lookup)
        if op == 'add':
            return lhs + rhs
        elif op == 'sub':
            return lhs - rhs
        elif op == 'mul':
            return lhs * rhs
        elif op == 'div':
            return lhs / rhs
        elif op == 'shl':
            return lhs << rhs
        elif op == 'shr':
            return lhs >> rhs
    elif op == 'neg':
        sub = interp(tree.children[0], lookup)
        return -sub
    elif op == 'num':
        return int(tree.children[0])
    elif op == 'var':
        return lookup(tree.children[0])
    elif op == 'if':
        cond = interp(tree.children[0], lookup)
        true = interp(tree.children[1], lookup)
        false = interp(tree.children[2], lookup)
        return (cond != 0) * true + (cond == 0) * false
    elif op == 'get':
        index = interp(tree.children[0], lookup)
        # print("array", tree.children[1])
        array = interp(tree.children[1], lookup)
        current = 0
        for i in range(len(array)):
            current = current + (index == i) * array[i]
        return current
    elif op == 'array':
        array = []
        # print("children", tree.children)
        for c in tree.children:
            array.append(interp(c, lookup))
        return array

parser = lark.Lark(GRAMMAR)
env = {'a': 3}
tree = parser.parse("get 1 [1, 2 * 2, a, 4]")
# print(tree)
# print(parser.parse("x * 10"))
# print(interp(tree, lambda v: env[v]))

def testLark(): 
    env = {'x': 2, 'y': -17}
    answer = interp(tree, lambda v: env[v])
    print(answer)

def z3_expr(tree,vars=None):
    vars = dict(vars) if vars else {}
    def get_var(name):
        if name in vars:
            return vars[name]
        else:
            v = z3.BitVec(name, 8)
            vars[name]=v
            return v
    return interp(tree, get_var), vars

def testing(exp1, exp2):
    tree1 = parser.parse(exp1)
    tree2 = parser.parse(exp2)
    expr1, vars1 = z3_expr(tree1)
    expr2, vars2 = z3_expr(tree2, vars1)

    plain_vars = {k: v for k, v in vars1.items()
              if not k.startswith('h')}
    goal = z3.ForAll(
        list(plain_vars.values()),  # need z3 objects
        expr1 == expr2,  # ...the two expressions produce equal results.
        )
    print(solve(goal))


if __name__ == "__main__":
    # sketching()
    # tree1 = parser.parse("x * 10")
    # tree2 = parser.parse("x << h1 + x << h2")
    # expr1, vars1 = z3_expr(tree1)
    # expr2, vars2 = z3_expr(tree2, vars1)
    # print(expr1, vars1)
    # print(expr2, vars2)

    testing("x * 10", "get h1 [x * 3, x * 4, x * 10]")
    testing("x * 6", "(get h1 [x * 3, x * 4, x * 10]) - (get h2 [x * 3, x * 4, x * 10])")
    