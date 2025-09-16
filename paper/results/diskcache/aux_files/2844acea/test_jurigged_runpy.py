import sys
import os
import tempfile
import ast
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import jurigged.runpy
import jurigged.rescript


# Test 1: _ModifiedArgv0 context manager properties
@given(st.text(min_size=1))
def test_modified_argv0_roundtrip(new_value):
    """Test that sys.argv[0] is properly restored after context exit."""
    original_argv0 = sys.argv[0]
    
    modifier = jurigged.runpy._ModifiedArgv0(new_value)
    
    # Test entering the context
    modifier.__enter__()
    assert sys.argv[0] == new_value
    
    # Test exiting the context
    modifier.__exit__(None, None, None)
    assert sys.argv[0] == original_argv0


@given(st.text(min_size=1))
def test_modified_argv0_no_nesting(value):
    """Test that _ModifiedArgv0 prevents nested usage."""
    modifier = jurigged.runpy._ModifiedArgv0(value)
    
    modifier.__enter__()
    try:
        # Should raise RuntimeError on second enter
        try:
            modifier.__enter__()
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "Already preserving saved value" in str(e)
    finally:
        modifier.__exit__(None, None, None)


# Test 2: _get_module_details relative module name validation
@given(st.text(min_size=1).filter(lambda x: not x.startswith('.')))
def test_get_module_details_accepts_absolute(mod_name):
    """Test that non-relative module names don't immediately fail."""
    try:
        jurigged.runpy._get_module_details(mod_name)
    except ImportError as e:
        # It's okay to fail for other reasons (module not found)
        # but not for being relative
        assert "Relative module names not supported" not in str(e)
    except Exception:
        # Other exceptions are fine - we're just testing the relative check
        pass


@given(st.text(min_size=1).map(lambda x: '.' + x))
def test_get_module_details_rejects_relative(mod_name):
    """Test that relative module names (starting with .) are rejected."""
    try:
        jurigged.runpy._get_module_details(mod_name)
        assert False, f"Should have rejected relative module name: {mod_name}"
    except ImportError as e:
        assert "Relative module names not supported" in str(e)


# Test 3: split_script properties
def generate_python_script():
    """Generate valid Python scripts with functions/classes."""
    # Simple templates for valid Python code
    templates = [
        "def func{i}():\n    pass\n",
        "class Class{i}:\n    pass\n",
        "async def async_func{i}():\n    pass\n",
        "x = {i}\n",
        "print({i})\n",
    ]
    
    return st.lists(
        st.sampled_from(templates),
        min_size=1,
        max_size=10
    ).map(lambda parts: ''.join(part.format(i=i) for i, part in enumerate(parts)))


@given(generate_python_script())
@settings(max_examples=100)
def test_split_script_returns_valid_code_objects(script_content):
    """Test that split_script returns two valid compiled code objects."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        f.flush()
        temp_path = f.name
    
    try:
        result = jurigged.rescript.split_script(temp_path)
        
        # Should return a tuple of two items
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        # Both should be code objects
        import types
        assert isinstance(result[0], types.CodeType)
        assert isinstance(result[1], types.CodeType)
        
    finally:
        os.unlink(temp_path)


@given(st.integers(min_value=1, max_value=5))
def test_split_script_splits_at_last_definition(num_funcs):
    """Test that split happens after the last function/class definition."""
    # Build a script with known structure
    script_lines = []
    
    # Add some initial code
    script_lines.append("x = 0\n")
    
    # Add function definitions
    for i in range(num_funcs):
        script_lines.append(f"def func{i}():\n    return {i}\n")
    
    # Add code after definitions
    script_lines.append("y = 1\n")
    script_lines.append("z = 2\n")
    
    script_content = ''.join(script_lines)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        f.flush()
        temp_path = f.name
    
    try:
        before, after = jurigged.rescript.split_script(temp_path)
        
        # Parse the original to check our expectations
        tree = ast.parse(script_content)
        
        # Find last definition index
        last_def_idx = 0
        for i, stmt in enumerate(tree.body):
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                last_def_idx = i + 1
        
        # The split should separate at this point
        # We can't easily decompile, but we can execute and check behavior
        ns_before = {}
        exec(before, ns_before)
        
        # All functions should be defined in before
        for i in range(num_funcs):
            assert f'func{i}' in ns_before
        
        # The initial x=0 should be in before (comes before functions)
        assert 'x' in ns_before
        
        # y and z should NOT be in before (come after functions)
        assert 'y' not in ns_before
        assert 'z' not in ns_before
        
    finally:
        os.unlink(temp_path)


# Test 4: Edge case - script with no functions
@given(st.lists(st.integers(min_value=0, max_value=100), min_size=1, max_size=10))
def test_split_script_no_functions(values):
    """Test split_script with scripts containing no function definitions."""
    script_content = '\n'.join(f"var_{i} = {v}" for i, v in enumerate(values))
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        f.flush()
        temp_path = f.name
    
    try:
        before, after = jurigged.rescript.split_script(temp_path)
        
        # With no functions, everything should be in 'after'
        ns_before = {}
        exec(before, ns_before)
        
        ns_after = {}
        exec(after, ns_after)
        
        # All variables should be in after
        for i in range(len(values)):
            assert f'var_{i}' in ns_after
            assert ns_after[f'var_{i}'] == values[i]
        
    finally:
        os.unlink(temp_path)