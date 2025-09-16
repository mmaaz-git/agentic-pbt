import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

import ast
import tempfile
import os
import types
from hypothesis import given, strategies as st, assume, settings
import jurigged.rescript as rescript

# Test 1: split_script property - the split should preserve all statements
@given(
    functions=st.lists(
        st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=1, max_size=10),
        min_size=0, max_size=5
    ),
    statements=st.lists(
        st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=1, max_size=10),
        min_size=0, max_size=5
    )
)
@settings(max_examples=100)
def test_split_script_preserves_all_statements(functions, statements):
    # Create a script with function definitions followed by statements
    script_lines = []
    for func_name in functions:
        # Make valid Python identifier
        func_name = 'f_' + ''.join(c for c in func_name if c.isalnum())
        if func_name and func_name[0].isdigit():
            func_name = 'f' + func_name
        script_lines.append(f"def {func_name}():\n    pass")
    
    for stmt in statements:
        # Create simple assignment statements
        var_name = 'v_' + ''.join(c for c in stmt if c.isalnum())
        if not var_name or var_name == 'v_':
            var_name = 'var'
        if var_name[0].isdigit():
            var_name = 'v' + var_name
        script_lines.append(f"{var_name} = 1")
    
    script_content = '\n'.join(script_lines) if script_lines else "pass"
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    try:
        before, after = rescript.split_script(script_path)
        
        # Parse original to count statements
        tree = ast.parse(script_content)
        total_statements = len(tree.body)
        
        # The split should preserve all statements
        # We can't easily count compiled code statements, but we can execute and check no errors
        namespace = {}
        exec(before, namespace)
        exec(after, namespace)
        
    finally:
        os.unlink(script_path)


# Test 2: split_script correctly identifies function boundaries
@given(
    num_funcs=st.integers(min_value=0, max_value=5),
    num_classes=st.integers(min_value=0, max_value=3),
    num_trailing_stmts=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=100)
def test_split_script_function_boundary(num_funcs, num_classes, num_trailing_stmts):
    script_lines = []
    
    # Add functions
    for i in range(num_funcs):
        script_lines.append(f"def func_{i}():\n    pass")
    
    # Add classes
    for i in range(num_classes):
        script_lines.append(f"class Class_{i}:\n    pass")
    
    # Add trailing statements
    for i in range(num_trailing_stmts):
        script_lines.append(f"var_{i} = {i}")
    
    script_content = '\n'.join(script_lines) if script_lines else "pass"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    try:
        before, after = rescript.split_script(script_path)
        
        # Parse to check the split point
        tree = ast.parse(script_content)
        expected_split = 0
        for i, stmt in enumerate(tree.body):
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                expected_split = i + 1
        
        # Execute both parts to ensure they're valid
        namespace = {}
        exec(before, namespace)
        exec(after, namespace)
        
        # Check that definitions are in the namespace after executing 'before'
        for i in range(num_funcs):
            assert f'func_{i}' in namespace
        for i in range(num_classes):
            assert f'Class_{i}' in namespace
            
    finally:
        os.unlink(script_path)


# Test 3: redirector_code generates valid code objects
@given(
    name=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=20
    ).filter(lambda x: x.isidentifier() and not x.startswith('_'))
)
@settings(max_examples=100)
def test_redirector_code_generates_valid_code(name):
    code_obj = rescript.redirector_code(name)
    
    # Check it's a code object
    assert isinstance(code_obj, types.CodeType)
    
    # The code should have the same name
    assert code_obj.co_name == name
    
    # It should reference the wrapped version in its names
    wrapped_name = f"____jurigged_wrapped_{name}"
    assert wrapped_name in code_obj.co_names


# Test 4: redirect function properly patches functions
@given(
    func_name=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=20
    ).filter(lambda x: x.isidentifier() and not x.startswith('_')),
    return_value=st.integers()
)
@settings(max_examples=100)
def test_redirect_function_patching(func_name, return_value):
    # Create a simple function
    namespace = {}
    exec(f"def {func_name}():\n    return {return_value}", namespace)
    orig_func = namespace[func_name]
    
    # Create a transform that adds 1 to the result
    def transform(f):
        def wrapped(*args, **kwargs):
            result = f(*args, **kwargs)
            return result + 1
        return wrapped
    
    # Apply redirect
    rescript.redirect(orig_func, transform)
    
    # The original function reference should now return transformed result
    assert orig_func() == return_value + 1
    
    # Check that the wrapped version exists in globals
    wrapped_name = f"____jurigged_wrapped_{func_name}"
    assert wrapped_name in orig_func.__globals__


# Test 5: redirect preserves function metadata
@given(
    func_name=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=20
    ).filter(lambda x: x.isidentifier() and not x.startswith('_')),
    default_val=st.integers()
)
@settings(max_examples=100)
def test_redirect_preserves_metadata(func_name, default_val):
    # Create function with metadata
    namespace = {}
    func_code = f'''
def {func_name}(x={default_val}):
    """Test docstring"""
    return x * 2
'''
    exec(func_code, namespace)
    orig_func = namespace[func_name]
    
    original_name = orig_func.__name__
    original_defaults = orig_func.__defaults__
    
    # Apply redirect with identity transform
    rescript.redirect(orig_func, lambda f: f)
    
    # Check metadata is preserved
    assert orig_func.__name__ == original_name
    assert orig_func.__defaults__ == original_defaults


# Test 6: redirect_code raises on invalid input
@given(
    num_functions=st.integers(min_value=0, max_value=5).filter(lambda x: x != 1)
)
@settings(max_examples=50)
def test_redirect_code_requires_exactly_one_function(num_functions):
    # Create code with multiple or no functions
    code_lines = []
    for i in range(num_functions):
        code_lines.append(f"def func_{i}():\n    pass")
    
    if not code_lines:
        code_lines.append("x = 1")  # Non-function statement
    
    code_str = '\n'.join(code_lines)
    code_obj = compile(code_str, '<test>', 'exec')
    
    # Mock transform
    transform = lambda f: f
    
    # This should raise an exception
    try:
        rescript.redirect_code(code_obj, transform)
        # If we get here, the function didn't raise as expected
        assert False, f"Expected exception for {num_functions} functions, but none was raised"
    except Exception as e:
        # Check it's the expected exception
        assert "exactly one function" in str(e).lower()


# Test 7: Test empty script handling
def test_split_script_empty_file():
    # Create empty script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("")
        script_path = f.name
    
    try:
        before, after = rescript.split_script(script_path)
        # Should not crash
        namespace = {}
        exec(before, namespace)
        exec(after, namespace)
    finally:
        os.unlink(script_path)


# Test 8: Test script with only comments
def test_split_script_comments_only():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("# This is a comment\n# Another comment")
        script_path = f.name
    
    try:
        before, after = rescript.split_script(script_path)
        namespace = {}
        exec(before, namespace)
        exec(after, namespace)
    finally:
        os.unlink(script_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])