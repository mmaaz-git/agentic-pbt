#!/usr/bin/env python3
import ast

# Let's understand the AST structure for augmented assignments
code1 = "x += 1"
tree1 = ast.parse(code1)
print("AST for 'x += 1':")
print(ast.dump(tree1, indent=2))

print("\n" + "="*50 + "\n")

code2 = "x = x + 1"
tree2 = ast.parse(code2)
print("AST for 'x = x + 1':")
print(ast.dump(tree2, indent=2))