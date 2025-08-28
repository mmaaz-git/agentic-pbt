"""
Minimal reproduction of the bug in Cython.CodeWriter
"""

import Cython.CodeWriter as CW

# Create a binary operation node with None as left operand
pos = (0, 0)
right = CW.IntNode(pos=pos, value='2')

# This succeeds - binop_node doesn't validate operands
node = CW.binop_node(pos=pos, operator='or', operand1=None, operand2=right)
print(f"Created node: {node}")
print(f"Node type: {type(node).__name__}")
print(f"Node operand1: {node.operand1}")
print(f"Node operand2: {node.operand2}")

# But when we try to serialize it, CodeWriter crashes
writer = CW.CodeWriter()
try:
    result = writer.write(node)
    print(f"Result: {result.s}")
except Exception as e:
    print(f"\nError occurred: {type(e).__name__}")
    print(f"Error message: {e}")