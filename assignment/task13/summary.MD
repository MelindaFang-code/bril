### Summary
https://github.com/MelindaFang-code/bril/blob/main/assignment/task13/foo.py
We extended the program synthesizer built in class with the array initialization and access feature. In the new synthesizer, users can initialize an arbitrary length of array, and also access elements using indexing. We defined the grammar as "get index [ele1, ele2, ...]". To achieve this, we expand the "GRAMMAR" part and the "interp" function to unroll elements in the array recursively.

### Hardest Part
The most challenging part of this task is to define the grammar of array and represent array as constraint. We studied and experimented with Lark a lot to define the grammar of array. After defined array, we have to represent array access as arithmetic expressions.
Given an array of this format, and we want to access a specific element
`get h1 [1, 2, x]`
We translate it to
`(h1 == 0) * 1 + (h1 == 1) * 2 + (h1 == 2) * x`
It acts as an `if-else` style, only if h1 matches a specific index, the branch will be activated, and the result will be a specific element.


### Testing
For testing, we constructs some manual test cases. This covers cases such as array index being an variable and array elements being accessed as variables.