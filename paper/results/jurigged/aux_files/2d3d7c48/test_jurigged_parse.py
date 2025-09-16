#!/usr/bin/env python3
import ast
import sys
import os
from hypothesis import given, strategies as st, assume, settings

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
                           'try', 'while', 'with', 'yield']
    )

# Strategy for simple Python expressions
@st.composite
def simple_expression(draw):
    return draw(st.one_of(
        st.integers(min_value=-1000, max_value=1000).map(str),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000).map(str),
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=5).map(lambda s: f'"{s}"'),
        python_identifier(),
    ))

# Property 1: free variables = read - assigned
@given(
    assigned=st.sets(python_identifier(), min_size=0, max_size=10),
    read=st.sets(python_identifier(), min_size=0, max_size=10)
)
def test_free_variables_property(assigned, read):
    v = Variables(assigned=assigned, read=read)
    assert v.free == read - assigned
    

# Property 2: Variables.__or__ unions correctly
@given(
    assigned1=st.sets(python_identifier(), min_size=0, max_size=5),
    read1=st.sets(python_identifier(), min_size=0, max_size=5),
    assigned2=st.sets(python_identifier(), min_size=0, max_size=5),
    read2=st.sets(python_identifier(), min_size=0, max_size=5)
)
def test_variables_or_operation(assigned1, read1, assigned2, read2):
    v1 = Variables(assigned=assigned1, read=read1)
    v2 = Variables(assigned=assigned2, read=read2)
    v3 = v1 | v2
    
    assert v3.assigned == assigned1 | assigned2
    assert v3.read == read1 | read2


# Property 3: Idempotence - analyzing the same code twice produces same results
@given(
    var_name=python_identifier(),
    value=simple_expression()
)
def test_idempotence_simple_assignment(var_name, value):
    code = f"{var_name} = {value}"
    tree = ast.parse(code)
    
    mapping1 = {}
    result1 = variables(tree, mapping1)
    
    mapping2 = {}
    result2 = variables(tree, mapping2)
    
    assert result1.assigned == result2.assigned
    assert result1.read == result2.read
    assert result1.free == result2.free


# Property 4: Function arguments are assigned within the function
@given(
    func_name=python_identifier(),
    arg_names=st.lists(python_identifier(), min_size=1, max_size=5, unique=True)
)
def test_function_arguments_are_assigned(func_name, arg_names):
    args_str = ', '.join(arg_names)
    code = f"def {func_name}({args_str}): pass"
    tree = ast.parse(code)
    
    mapping = {}
    result = variables(tree, mapping)
    
    # The function name itself should be assigned in the outer scope
    assert func_name in result.assigned
    
    # Check the function node mapping for argument assignments
    func_def = tree.body[0]
    if func_def in mapping:
        func_vars = mapping[func_def]
        for arg in arg_names:
            assert arg in func_vars.assigned


# Property 5: Variables used but not assigned are free
@given(
    var_names=st.lists(python_identifier(), min_size=1, max_size=5, unique=True)
)
def test_unassigned_variables_are_free(var_names):
    # Create code that uses variables without assigning them
    uses = ' + '.join(var_names)
    code = f"result = {uses}"
    tree = ast.parse(code)
    
    mapping = {}
    result = variables(tree, mapping)
    
    # All used variables should be in read set
    for var in var_names:
        assert var in result.read
    
    # All unassigned variables should be free
    for var in var_names:
        assert var in result.free


# Property 6: Nested functions - free variables propagate correctly
@given(
    outer_var=python_identifier(),
    inner_var=python_identifier(),
    used_var=python_identifier()
)
def test_nested_function_free_variables(outer_var, inner_var, used_var):
    assume(outer_var != inner_var != used_var)
    assume(outer_var != used_var)
    
    code = f"""
def outer():
    {outer_var} = 1
    def inner():
        {inner_var} = 2
        return {used_var}
    return inner
"""
    tree = ast.parse(code)
    
    mapping = {}
    result = variables(tree, mapping)
    
    # used_var should be free at module level since it's never assigned
    assert used_var in result.free


# Property 7: Class definitions handle __class__ specially
@given(class_name=python_identifier())
def test_class_defines_class_variable(class_name):
    code = f"""
class {class_name}:
    def method(self):
        return super()
"""
    tree = ast.parse(code)
    
    mapping = {}
    result = variables(tree, mapping)
    
    # The class name should be assigned
    assert class_name in result.assigned
    
    # __class__ should be handled internally for super() calls
    class_def = tree.body[0]
    if class_def in mapping:
        class_vars = mapping[class_def]
        assert "__class__" in class_vars.assigned


# Property 8: Store context creates assignments, Load context creates reads
@given(var_name=python_identifier())
def test_store_load_contexts(var_name):
    # Test assignment (Store context)
    store_code = f"{var_name} = 42"
    store_tree = ast.parse(store_code)
    store_result = variables(store_tree, {})
    assert var_name in store_result.assigned
    assert var_name not in store_result.read
    
    # Test read (Load context)
    load_code = f"print({var_name})"
    load_tree = ast.parse(load_code)
    load_result = variables(load_tree, {})
    assert var_name in load_result.read
    assert var_name not in load_result.assigned


if __name__ == "__main__":
    # Run all tests
    test_free_variables_property()
    test_variables_or_operation()
    test_idempotence_simple_assignment()
    test_function_arguments_are_assigned()
    test_unassigned_variables_are_free()
    test_nested_function_free_variables()
    test_class_defines_class_variable()
    test_store_load_contexts()
    print("All property tests completed!")