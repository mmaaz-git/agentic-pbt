# Bug Report: Cython.CodeWriter binop_node Accepts None Operands Causing Compiler Crash

**Target**: `Cython.CodeWriter.binop_node`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `binop_node` function in Cython.CodeWriter accepts None as operands without validation, creating malformed AST nodes that cause a CompilerCrash when CodeWriter attempts to serialize them.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import Cython.CodeWriter as CW

valid_operators = st.sampled_from(list(CW.binop_node_classes.keys()))
positions = st.tuples(st.integers(min_value=0, max_value=1000), 
                      st.integers(min_value=0, max_value=1000))

@given(operator=valid_operators, pos=positions)
def test_binop_with_none_operands(operator, pos):
    """Test binop_node behavior with None operands"""
    left = CW.IntNode(pos=pos, value='1')
    right = CW.IntNode(pos=pos, value='2')
    
    # Test with None left operand
    node = CW.binop_node(pos=pos, operator=operator, operand1=None, operand2=right)
    # This should either validate inputs or handle gracefully
    writer = CW.CodeWriter()
    result = writer.write(node)  # Crashes here
```

**Failing input**: `operator='or', pos=(0, 0)` (fails for all operators)

## Reproducing the Bug

```python
import Cython.CodeWriter as CW

pos = (0, 0)
right = CW.IntNode(pos=pos, value='2')

# binop_node accepts None without validation
node = CW.binop_node(pos=pos, operator='or', operand1=None, operand2=right)

# Crash occurs during serialization
writer = CW.CodeWriter()
result = writer.write(node)  # CompilerCrash
```

## Why This Is A Bug

The `binop_node` function is a public API that:
1. Accepts None operands without validation
2. Creates malformed AST nodes that cannot be visited
3. Causes a delayed crash during serialization rather than immediate validation
4. Provides unclear error messages that don't indicate the root cause

## Fix

```diff
def binop_node(pos, operator, operand1, operand2, inplace=False, **kwargs):
    # Construct binop node of appropriate class for
    # given operator.
+   if operand1 is None:
+       raise ValueError("operand1 cannot be None")
+   if operand2 is None:
+       raise ValueError("operand2 cannot be None")
    return binop_node_classes[operator](
        pos,
        operator=operator,
        operand1=operand1,
        operand2=operand2,
        inplace=inplace,
        **kwargs)
```