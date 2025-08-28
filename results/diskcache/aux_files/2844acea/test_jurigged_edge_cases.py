import sys
import os
import tempfile
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import jurigged.runpy
import jurigged.rescript


# Test edge case: Empty script file
def test_split_script_empty_file():
    """Test split_script with an empty Python file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("")  # Empty file
        f.flush()
        temp_path = f.name
    
    try:
        before, after = jurigged.rescript.split_script(temp_path)
        
        # Both should be valid code objects that do nothing
        ns_before = {}
        exec(before, ns_before)
        
        ns_after = {}  
        exec(after, ns_after)
        
        # No errors should occur
        assert True
    finally:
        os.unlink(temp_path)


# Test edge case: Script with only comments
@given(st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=1, max_size=50), min_size=1, max_size=5))
def test_split_script_only_comments(comment_lines):
    """Test split_script with files containing only comments."""
    script_content = '\n'.join(f"# {line}" for line in comment_lines)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        f.flush()
        temp_path = f.name
    
    try:
        before, after = jurigged.rescript.split_script(temp_path)
        
        # Should work without errors
        exec(before, {})
        exec(after, {})
        
    finally:
        os.unlink(temp_path)


# Test complex nesting scenarios
def test_split_script_nested_functions():
    """Test split_script with nested function definitions."""
    script_content = """
def outer():
    def inner():
        def deeply_nested():
            return 42
        return deeply_nested
    return inner

# Some code after
x = outer()()()
assert x == 42
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        f.flush()
        temp_path = f.name
    
    try:
        before, after = jurigged.rescript.split_script(temp_path)
        
        ns_before = {}
        exec(before, ns_before)
        
        # outer should be defined
        assert 'outer' in ns_before
        
        ns_after = dict(ns_before)  # Copy namespace
        exec(after, ns_after)
        
        # x should only be in after
        assert 'x' not in ns_before
        assert 'x' in ns_after
        assert ns_after['x'] == 42
        
    finally:
        os.unlink(temp_path)


# Test module name edge cases  
@given(st.text(alphabet='._', min_size=2, max_size=10))
def test_get_module_details_dots_and_underscores(mod_name):
    """Test _get_module_details with names containing only dots and underscores."""
    # Names starting with . should be rejected
    if mod_name.startswith('.'):
        try:
            jurigged.runpy._get_module_details(mod_name)
            assert False, f"Should reject: {mod_name}"
        except ImportError as e:
            assert "Relative module names not supported" in str(e)
    else:
        # Other names may fail for different reasons
        try:
            jurigged.runpy._get_module_details(mod_name)
        except ImportError:
            pass  # Expected for non-existent modules


# Test _ModifiedArgv0 with special values
@given(st.sampled_from([None, "", 0, [], {}]))
def test_modified_argv0_special_values(value):
    """Test _ModifiedArgv0 with non-string special values."""
    original = sys.argv[0]
    
    modifier = jurigged.runpy._ModifiedArgv0(value)
    modifier.__enter__()
    
    # Should accept any value
    assert sys.argv[0] == value
    
    modifier.__exit__(None, None, None)
    assert sys.argv[0] == original


# Test exception handling in _ModifiedArgv0
def test_modified_argv0_exception_handling():
    """Test that _ModifiedArgv0 restores argv even on exception."""
    original = sys.argv[0]
    
    class TestException(Exception):
        pass
    
    modifier = jurigged.runpy._ModifiedArgv0("test_value")
    modifier.__enter__()
    
    try:
        # Simulate an exception during context
        modifier.__exit__(TestException, TestException(), None)
    except:
        pass
    
    # argv[0] should still be restored
    assert sys.argv[0] == original


# Test Unicode and special characters in scripts
@given(st.text(alphabet='αβγδε', min_size=1, max_size=10))
def test_split_script_unicode_variable_names(greek_name):
    """Test split_script with Unicode variable names."""
    assume(greek_name.isidentifier())  # Must be valid Python identifier
    
    script_content = f"""
def {greek_name}():
    return 42

result = {greek_name}()
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script_content)
        f.flush()
        temp_path = f.name
    
    try:
        before, after = jurigged.rescript.split_script(temp_path)
        
        ns_before = {}
        exec(before, ns_before)
        assert greek_name in ns_before
        
        ns_after = dict(ns_before)
        exec(after, ns_after)
        assert 'result' in ns_after
        assert ns_after['result'] == 42
        
    finally:
        os.unlink(temp_path)