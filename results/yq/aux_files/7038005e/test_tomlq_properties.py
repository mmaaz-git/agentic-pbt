#!/usr/bin/env python3
"""
Property-based tests for yq.tomlq TOML processing functionality.
Testing round-trip properties, type preservation, and crash-resistance.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import io
import json
import subprocess
import tempfile
from datetime import datetime, date, time

import tomlkit
from hypothesis import given, strategies as st, settings, assume
from hypothesis.provisional import urls

# Import yq modules
import yq


# Strategy for valid TOML values
def toml_values():
    """Generate valid TOML values."""
    return st.recursive(
        st.one_of(
            st.text(min_size=0, max_size=100),  # strings
            st.integers(min_value=-2**31, max_value=2**31-1),  # integers
            st.floats(allow_nan=False, allow_infinity=False),  # floats  
            st.booleans(),  # booleans
            st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 1, 1)),  # datetimes
            st.dates(min_value=date(1900, 1, 1), max_value=date(2100, 1, 1)),  # dates
            st.times(),  # times
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=10),  # arrays
            st.dictionaries(  # tables
                st.text(min_size=1, max_size=20).filter(lambda s: s.isidentifier() or s.replace("-", "_").replace(".", "_").isidentifier()),
                children,
                max_size=10
            ),
        ),
        max_leaves=50
    )


# Strategy for valid TOML documents (must have dict at top level)
toml_documents = st.dictionaries(
    st.text(min_size=1, max_size=20).filter(lambda s: s.isidentifier() or s.replace("-", "_").replace(".", "_").isidentifier()),
    toml_values(),
    min_size=0,
    max_size=10
)


@given(toml_documents)
@settings(max_examples=200)
def test_toml_json_roundtrip_via_tomlkit(data):
    """Test that TOML data survives round-trip through JSON using tomlkit."""
    # Convert to TOML string
    toml_str = tomlkit.dumps(data)
    
    # Parse TOML string back
    parsed_from_toml = tomlkit.parse(toml_str)
    
    # Convert to JSON
    json_str = json.dumps(parsed_from_toml, cls=yq.JSONDateTimeEncoder)
    
    # Parse JSON back
    parsed_from_json = json.loads(json_str)
    
    # Convert back to TOML
    toml_output = tomlkit.dumps(parsed_from_json)
    
    # Parse the final TOML
    final_data = tomlkit.parse(toml_output)
    
    # Check data preservation
    # Note: tomlkit objects have special comparison, so we convert to regular dicts
    assert dict(parsed_from_toml) == dict(final_data)


@given(toml_documents)
@settings(max_examples=100)
def test_tomlq_cli_roundtrip(data):
    """Test that TOML data survives round-trip through the tomlq CLI tool."""
    # Skip if data contains datetime objects (CLI handles them differently)
    def has_datetime(obj):
        if isinstance(obj, (datetime, date, time)):
            return True
        if isinstance(obj, dict):
            return any(has_datetime(v) for v in obj.values())
        if isinstance(obj, list):
            return any(has_datetime(v) for v in obj)
        return False
    
    assume(not has_datetime(data))
    
    # Create initial TOML
    input_toml = tomlkit.dumps(data)
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(input_toml)
        input_file = f.name
    
    try:
        # Run through tomlq with identity filter and TOML output
        result = subprocess.run(
            [sys.executable, '-m', 'yq', '-t', '.', input_file],
            capture_output=True,
            text=True,
            env={'PYTHONPATH': '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages'}
        )
        
        # Check for errors
        if result.returncode != 0:
            # If jq is not installed, skip this test
            if "Is jq installed" in result.stderr:
                assume(False)
            raise Exception(f"tomlq failed: {result.stderr}")
        
        # Parse output TOML
        output_data = tomlkit.parse(result.stdout)
        
        # Compare data
        assert dict(data) == dict(output_data)
    finally:
        import os
        os.unlink(input_file)


@given(toml_documents)
@settings(max_examples=100)
def test_yq_function_toml_no_crash(data):
    """Test that the yq() function doesn't crash on valid TOML input."""
    # Create TOML string
    toml_str = tomlkit.dumps(data)
    
    # Create input/output streams
    input_stream = io.StringIO(toml_str)
    output_stream = io.StringIO()
    
    # Track if function was called successfully
    exit_code = None
    
    def capture_exit(code):
        nonlocal exit_code
        exit_code = code
    
    # Call yq function with TOML input
    try:
        yq.yq(
            input_streams=[input_stream],
            output_stream=output_stream,
            input_format="toml",
            output_format="json",
            jq_args=["."],  # Identity filter
            exit_func=capture_exit
        )
    except Exception as e:
        # Check if it's just jq not being installed
        if "jq" in str(e).lower() and "installed" in str(e).lower():
            assume(False)  # Skip test if jq not installed
        raise
    
    # Should have exited with code 0 for success
    assert exit_code == 0, f"yq exited with code {exit_code}"
    
    # Should have produced valid JSON output
    output = output_stream.getvalue()
    assert output, "No output produced"
    parsed_output = json.loads(output)
    
    # The output should match input data
    assert parsed_output == data


@given(toml_documents)
@settings(max_examples=100)  
def test_toml_to_json_type_preservation(data):
    """Test that TOML types are correctly preserved when converting to JSON."""
    # Skip complex datetime types for this test
    def has_datetime(obj):
        if isinstance(obj, (datetime, date, time)):
            return True
        if isinstance(obj, dict):
            return any(has_datetime(v) for v in obj.values())
        if isinstance(obj, list):
            return any(has_datetime(v) for v in obj)
        return False
    
    assume(not has_datetime(data))
    
    # Convert to TOML and back through JSON
    toml_str = tomlkit.dumps(data)
    parsed_toml = tomlkit.parse(toml_str)
    
    # Convert to JSON using yq's encoder
    json_str = json.dumps(parsed_toml, cls=yq.JSONDateTimeEncoder)
    parsed_json = json.loads(json_str)
    
    # Check type preservation
    def check_types(original, converted):
        if isinstance(original, bool):  # Check bool before int (bool is subclass of int)
            assert isinstance(converted, bool), f"Bool {original} became {type(converted)}"
            assert original == converted
        elif isinstance(original, int):
            assert isinstance(converted, int), f"Int {original} became {type(converted)}"
            assert original == converted
        elif isinstance(original, float):
            assert isinstance(converted, (int, float)), f"Float {original} became {type(converted)}"
            if isinstance(converted, float):
                assert abs(original - converted) < 1e-10
        elif isinstance(original, str):
            assert isinstance(converted, str), f"String {original} became {type(converted)}"
            assert original == converted
        elif isinstance(original, list):
            assert isinstance(converted, list), f"List became {type(converted)}"
            assert len(original) == len(converted)
            for orig_item, conv_item in zip(original, converted):
                check_types(orig_item, conv_item)
        elif isinstance(original, dict):
            assert isinstance(converted, dict), f"Dict became {type(converted)}"
            assert set(original.keys()) == set(converted.keys())
            for key in original:
                check_types(original[key], converted[key])
    
    check_types(data, parsed_json)


# Test for specific TOML features
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10).filter(lambda s: s.isidentifier()),
        st.lists(
            st.dictionaries(
                st.text(min_size=1, max_size=10).filter(lambda s: s.isidentifier()),
                st.one_of(st.text(), st.integers(), st.booleans()),
                min_size=1,
                max_size=3
            ),
            min_size=1,
            max_size=5
        ),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=50)
def test_array_of_tables_roundtrip(data):
    """Test that arrays of tables (TOML's [[table]] syntax) survive round-trip."""
    # Create TOML with array of tables
    doc = tomlkit.document()
    for key, tables_list in data.items():
        for table_dict in tables_list:
            table = tomlkit.table()
            for k, v in table_dict.items():
                table[k] = v
            if key not in doc:
                doc[key] = tomlkit.array()
            doc[key].append(table)
    
    toml_str = tomlkit.dumps(doc)
    
    # Parse back
    parsed = tomlkit.parse(toml_str)
    
    # Convert to JSON and back
    json_str = json.dumps(parsed, cls=yq.JSONDateTimeEncoder)
    from_json = json.loads(json_str)
    
    # Back to TOML
    final_toml = tomlkit.dumps(from_json)
    final_parsed = tomlkit.parse(final_toml)
    
    # Compare - the structure should be preserved
    assert dict(parsed) == dict(final_parsed)


# Test edge cases
def test_empty_toml_document():
    """Test that empty TOML documents are handled correctly."""
    empty_toml = ""
    parsed = tomlkit.parse(empty_toml)
    
    # Through JSON
    json_str = json.dumps(parsed, cls=yq.JSONDateTimeEncoder)
    from_json = json.loads(json_str)
    
    # Should be empty dict
    assert from_json == {}
    
    # Back to TOML
    final_toml = tomlkit.dumps(from_json)
    final_parsed = tomlkit.parse(final_toml)
    
    assert dict(final_parsed) == {}


def test_unicode_in_toml():
    """Test that Unicode characters in TOML are preserved."""
    data = {
        "unicode": "Hello 世界 🌍",
        "emoji": "🚀 Launch",
        "special": "café",
        "rtl": "مرحبا بالعالم"
    }
    
    # Round-trip test
    toml_str = tomlkit.dumps(data)
    parsed = tomlkit.parse(toml_str)
    
    json_str = json.dumps(parsed, cls=yq.JSONDateTimeEncoder)
    from_json = json.loads(json_str)
    
    final_toml = tomlkit.dumps(from_json)
    final_parsed = tomlkit.parse(final_toml)
    
    assert dict(final_parsed) == data


def test_special_float_values():
    """Test handling of special float values that TOML supports."""
    data = {
        "infinity": float('inf'),
        "neg_infinity": float('-inf'),
        # Note: TOML supports NaN but JSON doesn't by default
    }
    
    # Test TOML round-trip
    toml_str = tomlkit.dumps(data)
    parsed = tomlkit.parse(toml_str)
    
    # Note: yq.JSONDateTimeEncoder doesn't handle inf/nan specially
    # This might be a limitation we discover
    try:
        json_str = json.dumps(parsed, cls=yq.JSONDateTimeEncoder)
    except ValueError as e:
        # Expected - JSON doesn't support infinity
        assert "Out of range" in str(e) or "inf" in str(e).lower()


if __name__ == "__main__":
    # Run a quick test to ensure imports work
    print("Testing tomlq properties...")
    test_empty_toml_document()
    test_unicode_in_toml()
    test_special_float_values()
    print("Basic tests passed. Run with pytest for full property-based testing.")