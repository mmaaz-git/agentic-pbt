import re
from hypothesis import given, strategies as st, settings, assume
import click.shell_completion as shell_completion


# Look for edge cases in func_name generation
@given(st.text(min_size=1))
@settings(max_examples=2000)
def test_func_name_always_valid_identifier(prog_name):
    """func_name should always produce a valid shell identifier"""
    class TestComplete(shell_completion.ShellComplete):
        name = "test"
        source_template = "test"
        def get_completion_args(self):
            return [], ""
        def format_completion(self, item):
            return ""
    
    complete = TestComplete(None, {}, prog_name, "TEST")
    func_name = complete.func_name
    
    # Must be a valid shell identifier
    assert re.match(r'^[_a-zA-Z][_a-zA-Z0-9]*$', func_name), f"Invalid identifier: {func_name}"
    assert func_name.startswith("_")
    assert func_name.endswith("_completion")


@given(prog_name=st.text(min_size=1))
@settings(max_examples=2000)
def test_func_name_preserves_some_info(prog_name):
    """func_name should preserve some information from prog_name when possible"""
    class TestComplete(shell_completion.ShellComplete):
        name = "test"
        source_template = "test"
        def get_completion_args(self):
            return [], ""
        def format_completion(self, item):
            return ""
    
    complete = TestComplete(None, {}, prog_name, "TEST")
    func_name = complete.func_name
    
    # Check if alphanumeric characters are preserved
    prog_alphanum = re.sub(r'\W', '', prog_name, flags=re.ASCII)
    if prog_alphanum:
        # At least some characters should be preserved
        assert prog_alphanum.replace('-', '_') in func_name or prog_alphanum in func_name


# Test specific edge cases
def test_func_name_edge_cases():
    """Test specific edge cases for func_name"""
    test_cases = [
        ("", "_completion"),  # Empty prog_name
        ("123", "_123_completion"),  # Starts with digit
        ("--flag", "_flag_completion"),  # Starts with dashes
        ("-", "__completion"),  # Just dash
        ("@#$%", "_completion"),  # Only special chars
        ("hello-world", "_hello_world_completion"),  # Dash to underscore
        ("CAPS", "_CAPS_completion"),  # Capitals preserved
        ("with spaces", "_withspaces_completion"),  # Spaces removed
        ("unicode_テスト", "_unicode__completion"),  # Non-ASCII removed
        ("../../etc/passwd", "_etcpasswd_completion"),  # Path traversal
    ]
    
    class TestComplete(shell_completion.ShellComplete):
        name = "test"
        source_template = "test"
        def get_completion_args(self):
            return [], ""
        def format_completion(self, item):
            return ""
    
    for prog_name, expected in test_cases:
        complete = TestComplete(None, {}, prog_name, "TEST")
        func_name = complete.func_name
        print(f"prog_name={repr(prog_name):30} -> func_name={repr(func_name):30} (expected: {expected})")
        
        # Must be valid identifier
        assert re.match(r'^[_a-zA-Z][_a-zA-Z0-9]*$', func_name), f"Invalid: {func_name}"
        
        # Check against expected
        if expected != func_name:
            print(f"  MISMATCH: Expected {expected}, got {func_name}")


def test_func_name_empty_string():
    """Test func_name with empty prog_name"""
    class TestComplete(shell_completion.ShellComplete):
        name = "test" 
        source_template = "test"
        def get_completion_args(self):
            return [], ""
        def format_completion(self, item):
            return ""
    
    complete = TestComplete(None, {}, "", "TEST")
    func_name = complete.func_name
    print(f"Empty prog_name gives: {repr(func_name)}")
    assert func_name == "__completion"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-k", "edge"])