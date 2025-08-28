"""Property-based testing for json.tool module"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import math


# Generate valid JSON values
json_values = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.text(min_size=0, max_size=100),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
            children,
            max_size=10
        ),
    ),
    max_leaves=50
)


@composite
def sorted_dict_keys(draw):
    """Generate dictionaries with sortable string keys"""
    keys = draw(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10, unique=True))
    values = draw(st.lists(json_values, min_size=len(keys), max_size=len(keys)))
    return dict(zip(keys, values))


def run_json_tool(input_data, args=None):
    """Run json.tool on input data and return output"""
    args = args or []
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        input_file = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'json.tool'] + args + [input_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return None, result.stderr
        return result.stdout, None
    finally:
        Path(input_file).unlink()


@given(json_values)
@settings(max_examples=200)
def test_round_trip_property(data):
    """Test that json.tool preserves data through round-trip"""
    output, error = run_json_tool(data)
    if error:
        # json.tool should handle all valid JSON
        assert False, f"json.tool failed on valid JSON: {error}"
    
    # Parse the output back
    parsed = json.loads(output)
    
    # The parsed data should equal the original
    assert parsed == data, f"Round-trip failed: {data} != {parsed}"


@given(sorted_dict_keys())
@settings(max_examples=100)
def test_sort_keys_property(data):
    """Test that --sort-keys actually sorts dictionary keys"""
    output, error = run_json_tool(data, ['--sort-keys'])
    if error:
        assert False, f"json.tool failed with --sort-keys: {error}"
    
    parsed = json.loads(output)
    
    # Check that keys are sorted at all levels
    def check_sorted_keys(obj):
        if isinstance(obj, dict):
            keys = list(obj.keys())
            assert keys == sorted(keys), f"Keys not sorted: {keys}"
            for value in obj.values():
                check_sorted_keys(value)
        elif isinstance(obj, list):
            for item in obj:
                check_sorted_keys(item)
    
    check_sorted_keys(parsed)


@given(st.lists(json_values, min_size=1, max_size=10))
@settings(max_examples=100)
def test_json_lines_property(data_list):
    """Test that --json-lines produces valid JSON on each line"""
    # Create JSON Lines input
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for item in data_list:
            json.dump(item, f)
            f.write('\n')
        input_file = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'json.tool', '--json-lines', '--no-indent', input_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            assert False, f"json.tool failed with --json-lines: {result.stderr}"
        
        # Each line should be valid JSON
        lines = result.stdout.strip().split('\n')
        parsed_items = []
        for line in lines:
            if line:  # Skip empty lines
                parsed_items.append(json.loads(line))
        
        assert parsed_items == data_list, f"JSON Lines round-trip failed"
    finally:
        Path(input_file).unlink()


@given(json_values)
@settings(max_examples=100)
def test_compact_vs_normal_property(data):
    """Test that --compact produces equivalent JSON"""
    normal_output, normal_error = run_json_tool(data)
    compact_output, compact_error = run_json_tool(data, ['--compact'])
    
    if normal_error or compact_error:
        assert False, f"json.tool failed: normal={normal_error}, compact={compact_error}"
    
    # Both should parse to the same data
    normal_parsed = json.loads(normal_output)
    compact_parsed = json.loads(compact_output)
    
    assert normal_parsed == compact_parsed == data
    
    # Compact should have no unnecessary whitespace
    # Check that compact is actually more compact
    assert len(compact_output) <= len(normal_output)


@given(st.text(min_size=0, max_size=100))
@settings(max_examples=100)
def test_unicode_handling(text):
    """Test handling of Unicode characters with --no-ensure-ascii"""
    data = {"text": text}
    
    # Test with ASCII escaping (default)
    ascii_output, ascii_error = run_json_tool(data)
    
    # Test without ASCII escaping
    unicode_output, unicode_error = run_json_tool(data, ['--no-ensure-ascii'])
    
    if ascii_error or unicode_error:
        assert False, f"json.tool failed: ascii={ascii_error}, unicode={unicode_error}"
    
    # Both should parse to the same data
    ascii_parsed = json.loads(ascii_output)
    unicode_parsed = json.loads(unicode_output)
    
    assert ascii_parsed == unicode_parsed == data


@given(st.integers(min_value=0, max_value=20))
@settings(max_examples=50)
def test_indent_property(indent_size):
    """Test that --indent produces valid JSON with specified indentation"""
    data = {"key": ["value1", "value2"], "nested": {"a": 1, "b": 2}}
    
    result = subprocess.run(
        [sys.executable, '-m', 'json.tool', '--indent', str(indent_size)],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        timeout=5
    )
    
    if result.returncode != 0:
        assert False, f"json.tool failed with --indent {indent_size}: {result.stderr}"
    
    # Should still parse correctly
    parsed = json.loads(result.stdout)
    assert parsed == data
    
    # Check indentation (if indent > 0, lines should have proper spacing)
    if indent_size > 0:
        lines = result.stdout.split('\n')
        # Check that nested elements have indentation
        for line in lines:
            if line.strip() and line.strip() not in ['{', '}', '[', ']']:
                # Line should start with spaces if it's indented
                if line != line.lstrip():
                    spaces = len(line) - len(line.lstrip())
                    # Indentation should be a multiple of indent_size
                    assert spaces % indent_size == 0, f"Incorrect indentation: {spaces} not divisible by {indent_size}"


# Test for potential edge cases and bugs
@given(st.dictionaries(
    st.text(min_size=0, max_size=50),
    json_values,
    min_size=0,
    max_size=20
))
@settings(max_examples=100)
def test_empty_and_special_keys(data):
    """Test handling of edge case dictionary keys"""
    # Filter out truly empty keys as JSON doesn't support them
    if "" in data:
        assume(False)
    
    output, error = run_json_tool(data)
    
    if error:
        # Check if this is expected (e.g., empty string keys are invalid in JSON)
        if "" in data:
            return  # Expected to fail
        assert False, f"Unexpected error: {error}"
    
    parsed = json.loads(output)
    assert parsed == data


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])