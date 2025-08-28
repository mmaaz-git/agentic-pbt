#!/usr/bin/env python3
import ast
import sys

sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.parse import Variables, variables

# Test 1: Simple augmented assignment
print("Test 1: Augmented assignment (x += 1)")
code1 = "x += 1"
tree1 = ast.parse(code1)
result1 = variables(tree1, {})
print(f"  Assigned: {result1.assigned}")
print(f"  Read: {result1.read}")
print(f"  Free: {result1.free}")
print(f"  Expected: x should be in both assigned AND read (since x += 1 means x = x + 1)")
print(f"  Bug: x is only in assigned, not in read\n")

# Test 2: Regular assignment for comparison
print("Test 2: Regular assignment (x = x + 1)")
code2 = "x = x + 1"
tree2 = ast.parse(code2)
result2 = variables(tree2, {})
print(f"  Assigned: {result2.assigned}")
print(f"  Read: {result2.read}")
print(f"  Free: {result2.free}")
print(f"  This works correctly: x is in both assigned and read\n")

# Test 3: Various augmented operators
print("Test 3: Various augmented operators")
operators = ["+=", "-=", "*=", "/=", "//=", "%=", "**=", "&=", "|=", "^=", ">>=", "<<="]
for op in operators:
    code = f"y {op} 2"
    tree = ast.parse(code)
    result = variables(tree, {})
    print(f"  y {op} 2 -> Assigned: {result.assigned}, Read: {result.read}")

print("\nImpact: This bug means the parser incorrectly analyzes augmented assignments.")
print("It fails to recognize that these operations read the variable before writing.")
print("This could lead to incorrect free variable detection in code analysis tools.")