"""
Test variations of the None operand bug
"""

import Cython.CodeWriter as CW

pos = (0, 0)

# Test different operators
operators = ['+', '-', '*', '/', 'and', 'or', '&', '|']

for op in operators:
    # Test with None left operand
    try:
        right = CW.IntNode(pos=pos, value='2')
        node = CW.binop_node(pos=pos, operator=op, operand1=None, operand2=right)
        writer = CW.CodeWriter()
        result = writer.write(node)
        print(f"✓ {op} with None left: OK")
    except Exception as e:
        print(f"✗ {op} with None left: {type(e).__name__}")
    
    # Test with None right operand
    try:
        left = CW.IntNode(pos=pos, value='1')
        node = CW.binop_node(pos=pos, operator=op, operand1=left, operand2=None)
        writer = CW.CodeWriter()
        result = writer.write(node)
        print(f"✓ {op} with None right: OK")
    except Exception as e:
        print(f"✗ {op} with None right: {type(e).__name__}")
        
    # Test with both None
    try:
        node = CW.binop_node(pos=pos, operator=op, operand1=None, operand2=None)
        writer = CW.CodeWriter()
        result = writer.write(node)
        print(f"✓ {op} with both None: OK")
    except Exception as e:
        print(f"✗ {op} with both None: {type(e).__name__}")