### Summary

We implemented just-in-time compiler feature in `brili_jit.ts`. We traced the execution of a function called `myloop` for 5 times, find the most frequent trace, perform some optimizations on that, and plug it back to the front of that function. In order to roll-back when some conditions is not met, we replace all `br` operations with a `guard` operation. The guard operation takes a variable called `condition`, and the condition is set to either the same as the argument of `br`, or negation of that argument, if we traced the second branch. When the guard operation failed, it jumps to a `failed` label inserted at the beginning of the original instructions. When we plug the instructions back to the function, we insert an `speculate` operation at the beginning of the trace and a `commit` before the `ret` instruction of the trace.

We implemented the dead code elimination optimization on the trace. If a variable is only used in one branch but not the other, when we eliminate the branch, we will be able to eliminate that variable and other variables that are only used by that. We have also written an example bril code that demonstrates the optimization. 

### Hardest Part
The most challenging part of this task is to figure out how just-in-time compiler works. Bril has provided good abstractions for us, the `speculate`, `guard`, and `commit` operations. With these operations, we can easily enter a speculation mode, and discard the computation when the assumption of the code is incorrect. It's also a little tricky to insert the trace back to the function, we spent a bit of time studying what should `guard` take as its argument.

### Testing
We create a test case in "test_jit.bril". It has some dead code that could be eliminated in the function myloop if the program executes the most commonly used branch. Here is the pseudocode. We tried different inputs such as 45 and 100 that would cause the guard to be evaluated differently and compared both the results and the dynamic instruction count.
```
function myloop(x) {
  y = x + 1;
  a1 = 8;
  a2 = a1 + a1;
  a3 = a2 + a2;
  a4 = a3 + a3;
  if (x < 50) {
    z = y - 1;
  } else {
    z = y + a4;
  }
  return z;
}

function main(a) {
  index = 0;
  result = 0;
  for (index in range (a)) {
    result = myloop(index);
  }
  print(result);
}
```
After the Optimization the bril code looks like
```
[
  { op: "speculate" },
  { dest: "one", op: "const", type: "int", value: 1 },
  { args: [ "x", "one" ], dest: "y", op: "add", type: "int" },
  { dest: "three", op: "const", type: "int", value: 50 },
  { args: [ "x", "three" ], dest: "cond", op: "lt", type: "bool" },
  { dest: "condition", op: "id", type: "bool", args: [ "cond" ] },
  { op: "guard", args: [ "condition" ], labels: [ "failed" ] },
  { args: [ "y", "one" ], dest: "z", op: "sub", type: "int" },
  { op: "commit" },
  { args: [ "z" ], op: "ret" },
  { label: "failed" },
  { dest: "one", op: "const", type: "int", value: 1 },
  { args: [ "x", "one" ], dest: "y", op: "add", type: "int" },
  { dest: "three", op: "const", type: "int", value: 50 },
  { args: [ "x", "three" ], dest: "cond", op: "lt", type: "bool" },
  { dest: "a1", op: "const", type: "int", value: 8 },
  { args: [ "a1", "a1" ], dest: "a2", op: "add", type: "int" },
  { args: [ "a2", "a2" ], dest: "a3", op: "add", type: "int" },
  { args: [ "a3", "a3" ], dest: "a4", op: "add", type: "int" },
  { args: [ "cond" ], labels: [ "small", "big" ], op: "br" },
  { label: "small" },
  { args: [ "y", "one" ], dest: "z", op: "sub", type: "int" },
  { args: [ "z" ], op: "ret" },
  { label: "big" },
  { args: [ "y", "a4" ], dest: "z", op: "add", type: "int" },
  { args: [ "z" ], op: "ret" }
]
```
so it is clear that our algorithm successfully eliminates the dead code if we branch to the ".small" branch. If we run the program with argument = 45, the instruction count of our program is 686, whereas that of the original bril.ts is 726. However, if we run the program with argument being 100, the instruction count is 1911 vs 1606, since we need to execute extra instructions such as "guard". "speculate", and we also failed the guard so we waste executing instructions that will be rolled back eventually.