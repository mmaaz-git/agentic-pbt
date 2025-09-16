#!/usr/bin/env python3
import ast
import sys
import os
from hypothesis import given, strategies as st, assume, settings, example

sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.parse import Variables, variables


# Strategy for generating valid Python variable names
def python_identifier():
    first_char = st.sampled_from('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')
    other_chars = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_', min_size=0, max_size=10)
    return st.builds(lambda f, o: f + o, first_char, other_chars).filter(
        lambda x: x not in ['False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 
                           'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
                           'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 
                           'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 
                           'try', 'while', 'with', 'yield', '__class__', 'super']
    )


# Property: Del statements should affect assignments 
@given(var_name=python_identifier())
def test_del_statement_handling(var_name):
    code = f"""
{var_name} = 42
del {var_name}
"""
    tree = ast.parse(code)
    result = variables(tree, {})
    
    # After del, the variable might be considered in a Del context
    # Let's see how it's handled
    assert var_name in result.assigned


# Property: Comprehensions should handle variable scoping
@given(
    iter_var=python_identifier(),
    list_var=python_identifier()
)
def test_list_comprehension_scoping(iter_var, list_var):
    assume(iter_var != list_var)
    
    code = f"result = [{iter_var} for {iter_var} in {list_var}]"
    tree = ast.parse(code)
    result = variables(tree, {})
    
    # list_var should be read
    assert list_var in result.read
    # iter_var in comprehension shouldn't leak to outer scope in Python 3
    # But the parser might handle this differently
    print(f"Assigned: {result.assigned}, Read: {result.read}, Free: {result.free}")


# Property: Global and nonlocal declarations
@given(
    global_var=python_identifier(),
    local_var=python_identifier()
)
def test_global_nonlocal_declarations(global_var, local_var):
    assume(global_var != local_var)
    
    code = f"""
def outer():
    global {global_var}
    {global_var} = 1
    {local_var} = 2
    def inner():
        nonlocal {local_var}
        {local_var} = 3
    return inner
"""
    tree = ast.parse(code)
    mapping = {}
    result = variables(tree, mapping)
    
    # Check how global/nonlocal are handled
    print(f"Module level - Assigned: {result.assigned}, Read: {result.read}, Free: {result.free}")


# Property: Lambda functions
@given(
    param=python_identifier(),
    free_var=python_identifier()
)
def test_lambda_function_variables(param, free_var):
    assume(param != free_var)
    
    code = f"f = lambda {param}: {param} + {free_var}"
    tree = ast.parse(code)
    result = variables(tree, {})
    
    # free_var should be free since it's not assigned
    assert free_var in result.free
    # param shouldn't be free at module level
    assert param not in result.free


# Property: Augmented assignments (+=, -=, etc.)
@given(var_name=python_identifier())
def test_augmented_assignment(var_name):
    code = f"{var_name} += 1"
    tree = ast.parse(code)
    result = variables(tree, {})
    
    # Augmented assignment both reads and writes
    # The variable should be both assigned and read
    print(f"Aug assign - Assigned: {result.assigned}, Read: {result.read}")
    # Since it reads before assigning, it should be free
    assert var_name in result.free


# Property: Multiple assignment targets
@given(
    var1=python_identifier(),
    var2=python_identifier(),
    var3=python_identifier()
)
def test_multiple_assignment_targets(var1, var2, var3):
    assume(len({var1, var2, var3}) == 3)  # All different
    
    code = f"{var1} = {var2} = {var3} = 42"
    tree = ast.parse(code)
    result = variables(tree, {})
    
    # All should be assigned
    assert var1 in result.assigned
    assert var2 in result.assigned
    assert var3 in result.assigned


# Property: Tuple unpacking
@given(
    var1=python_identifier(),
    var2=python_identifier(),
    source=python_identifier()
)
def test_tuple_unpacking(var1, var2, source):
    assume(len({var1, var2, source}) == 3)
    
    code = f"{var1}, {var2} = {source}"
    tree = ast.parse(code)
    result = variables(tree, {})
    
    assert var1 in result.assigned
    assert var2 in result.assigned
    assert source in result.read
    assert source in result.free


# Property: Try-except blocks
@given(
    exc_var=python_identifier(),
    normal_var=python_identifier()
)
def test_try_except_variables(exc_var, normal_var):
    assume(exc_var != normal_var)
    
    code = f"""
try:
    {normal_var} = risky_operation()
except Exception as {exc_var}:
    print({exc_var})
"""
    tree = ast.parse(code)
    result = variables(tree, {})
    
    # Both should be assigned
    assert normal_var in result.assigned
    assert exc_var in result.assigned
    # risky_operation should be read/free
    assert "risky_operation" in result.free


# Property: With statements
@given(
    context_var=python_identifier(),
    resource=python_identifier()
)
def test_with_statement_variables(context_var, resource):
    assume(context_var != resource)
    
    code = f"""
with {resource} as {context_var}:
    print({context_var})
"""
    tree = ast.parse(code)
    result = variables(tree, {})
    
    assert context_var in result.assigned
    assert resource in result.read
    assert resource in result.free


# Property: Decorators
@given(
    func_name=python_identifier(),
    decorator=python_identifier()
)
def test_decorator_variables(func_name, decorator):
    assume(func_name != decorator)
    
    code = f"""
@{decorator}
def {func_name}():
    pass
"""
    tree = ast.parse(code)
    result = variables(tree, {})
    
    assert func_name in result.assigned
    assert decorator in result.read
    assert decorator in result.free


# Property: Star expressions in assignments
@given(
    first=python_identifier(),
    rest=python_identifier(),
    source=python_identifier()
)
def test_star_expression(first, rest, source):
    assume(len({first, rest, source}) == 3)
    
    code = f"{first}, *{rest} = {source}"
    tree = ast.parse(code)
    result = variables(tree, {})
    
    assert first in result.assigned
    assert rest in result.assigned
    assert source in result.read


# Property: Walrus operator (assignment expression) - Python 3.8+
@given(var_name=python_identifier())
@settings(max_examples=50)
def test_walrus_operator(var_name):
    code = f"if ({var_name} := get_value()): print({var_name})"
    try:
        tree = ast.parse(code)
        result = variables(tree, {})
        
        # var_name should be both assigned and read
        assert var_name in result.assigned
        assert var_name in result.read
        assert "get_value" in result.free
    except SyntaxError:
        # Older Python versions don't support walrus
        pass


# Property: Async functions and await
@given(
    func_name=python_identifier(),
    var_name=python_identifier()
)
def test_async_function(func_name, var_name):
    code = f"""
async def {func_name}():
    {var_name} = await something()
    return {var_name}
"""
    tree = ast.parse(code)
    mapping = {}
    result = variables(tree, mapping)
    
    assert func_name in result.assigned
    # Check function body variables
    if tree.body[0] in mapping:
        func_vars = mapping[tree.body[0]]
        assert var_name in func_vars.assigned
        assert "something" in func_vars.read


# Property: Empty collections and corner cases
def test_empty_and_corner_cases():
    # Empty code
    tree = ast.parse("")
    result = variables(tree, {})
    assert result.assigned == set()
    assert result.read == set()
    assert result.free == set()
    
    # Just a pass statement
    tree = ast.parse("pass")
    result = variables(tree, {})
    assert result.assigned == set()
    assert result.read == set()
    assert result.free == set()
    
    # Single expression
    tree = ast.parse("42")
    result = variables(tree, {})
    assert result.assigned == set()
    assert result.read == set()
    assert result.free == set()


# Property: Complex nested structures
@given(
    outer=python_identifier(),
    middle=python_identifier(),
    inner=python_identifier(),
    free=python_identifier()
)
@settings(max_examples=20)
def test_deeply_nested_functions(outer, middle, inner, free):
    assume(len({outer, middle, inner, free}) == 4)
    
    code = f"""
def {outer}():
    x = 1
    def {middle}():
        y = 2
        def {inner}():
            z = 3
            return x + y + z + {free}
        return {inner}
    return {middle}
"""
    tree = ast.parse(code)
    result = variables(tree, {})
    
    # Only the outermost function name should be assigned at module level
    assert outer in result.assigned
    # The free variable should be free at module level
    assert free in result.free


if __name__ == "__main__":
    # Run with pytest for better output
    import pytest
    pytest.main([__file__, '-v', '--tb=short', '-x'])