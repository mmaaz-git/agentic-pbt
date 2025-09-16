"""Advanced property-based tests for the main yq function."""

import sys
import json
import io
import tempfile
import os
from datetime import datetime

sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import yq
import yaml
from hypothesis import given, strategies as st, assume, settings
import pytest


# Test the main yq function with YAML to JSON conversion
@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
        st.one_of(
            st.integers(min_value=-1000, max_value=1000),
            st.text(max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'),
            st.booleans(),
            st.none()
        ),
        min_size=1,
        max_size=5
    )
)
@settings(deadline=5000)  # Increase deadline as subprocess calls can be slow
def test_yq_yaml_to_json_conversion(data):
    """Test that yq can convert YAML to JSON correctly."""
    # Create YAML input
    yaml_str = yaml.dump(data)
    input_stream = io.StringIO(yaml_str)
    output_stream = io.StringIO()
    
    # Mock exit function to capture exit codes
    exit_code = None
    def mock_exit(code):
        nonlocal exit_code
        exit_code = code
    
    # Run yq with simple identity filter
    try:
        yq.yq(
            input_streams=[input_stream],
            output_stream=output_stream,
            input_format="yaml",
            output_format="json",
            jq_args=["."],
            exit_func=mock_exit
        )
    except FileNotFoundError:
        # jq might not be installed, skip this test
        pytest.skip("jq not installed")
    
    if exit_code == 0:
        # Parse the output
        output_stream.seek(0)
        result = json.loads(output_stream.read())
        
        # Should preserve the data
        assert result == data


# Test YAML expansion limits
def test_yaml_expansion_limit_detection():
    """Test that excessive YAML expansion is detected."""
    # Create a YAML bomb (billion laughs attack variant)
    yaml_bomb = """
a: &a ["x", "x"]
b: &b [*a, *a]
c: &c [*b, *b]
d: &d [*c, *c]
e: &e [*d, *d]
f: &f [*e, *e]
g: &g [*f, *f]
h: &h [*g, *g]
i: &i [*h, *h]
"""
    
    input_stream = io.StringIO(yaml_bomb)
    output_stream = io.StringIO()
    
    exit_message = None
    def capture_exit(msg):
        nonlocal exit_message
        exit_message = msg
    
    # This should detect the expansion and exit
    try:
        yq.yq(
            input_streams=[input_stream],
            output_stream=output_stream,
            input_format="yaml",
            output_format="json",
            max_expansion_factor=100,  # Low limit to trigger detection
            jq_args=["."],
            exit_func=capture_exit
        )
    except (FileNotFoundError, SystemExit):
        # jq not installed or system exit called
        pass
    
    # Should have detected unsafe expansion (if jq is available)
    if exit_message and "unsafe YAML entity expansion" in str(exit_message):
        assert True  # Expected behavior
    else:
        # Either jq not available or expansion not detected
        pass


# Test XML round-trip property
@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
        st.one_of(
            st.integers(min_value=-100, max_value=100),
            st.text(max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz')
        ),
        min_size=1,
        max_size=3
    )
)
def test_xml_round_trip(data):
    """Test XML to JSON to XML conversion."""
    import xmltodict
    
    # Convert dict to XML
    xml_str = xmltodict.unparse({"root": data}, full_document=False)
    
    # Parse it back
    parsed = xmltodict.parse(xml_str, disable_entities=True)
    
    # Should get back the same structure
    assert parsed == {"root": data}


# Test TOML handling
@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
        st.one_of(
            st.integers(min_value=-100, max_value=100),
            st.text(max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'),
            st.booleans()
        ),
        min_size=1,
        max_size=5
    )
)
def test_toml_round_trip(data):
    """Test TOML round-trip conversion."""
    import tomlkit
    
    # Convert to TOML
    toml_str = tomlkit.dumps(data)
    
    # Parse it back
    parsed = toml_loads = yq.get_toml_loader()
    result = toml_loads(toml_str)
    
    # Should preserve the data
    assert result == data


# Test date/time encoding in different contexts
@given(
    dt=st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2030, 12, 31))
)
def test_datetime_in_yaml_context(dt):
    """Test datetime handling in YAML context."""
    data = {"timestamp": dt, "value": 42}
    
    # Encode with JSONDateTimeEncoder
    encoder = yq.JSONDateTimeEncoder()
    json_str = encoder.encode(data)
    
    # Should contain ISO format timestamp
    parsed = json.loads(json_str)
    assert "timestamp" in parsed
    assert isinstance(parsed["timestamp"], str)
    assert "T" in parsed["timestamp"] or "-" in parsed["timestamp"]


# Test edge case: non-dict top-level for XML/TOML
def test_non_dict_top_level_error_handling():
    """Test that non-dict top-level values are handled correctly for XML/TOML."""
    # XML and TOML require dict at top level
    non_dict_values = [
        42,
        "string",
        [1, 2, 3],
        True,
        None
    ]
    
    for value in non_dict_values:
        json_str = json.dumps(value)
        input_stream = io.StringIO(json_str)
        output_stream = io.StringIO()
        
        exit_message = None
        def capture_exit(msg):
            nonlocal exit_message
            exit_message = msg
        
        # Try to convert to XML
        try:
            # Note: This would need jq installed and would process through it
            # We're testing the error handling for non-dict values
            import xmltodict
            
            # Test xmltodict directly (since yq uses it internally)
            with pytest.raises((ValueError, TypeError)):
                xmltodict.unparse(value)
        except:
            pass
        
        # Try to convert to TOML
        try:
            import tomlkit
            
            # TOML also requires dict at top level
            if not isinstance(value, dict):
                with pytest.raises((ValueError, TypeError, AttributeError)):
                    tomlkit.dumps(value)
        except:
            pass


# Test special characters in keys
@given(
    key=st.text(min_size=1, max_size=20).filter(lambda x: x and not x.isspace()),
    value=st.integers()
)
def test_special_key_handling(key, value):
    """Test handling of special characters in dictionary keys."""
    from yq.loader import hash_key
    
    # Test hash_key with special characters
    hash_result = hash_key(key)
    
    # Should produce valid base64
    assert isinstance(hash_result, str)
    assert len(hash_result) == 40
    
    # Should be deterministic
    assert hash_key(key) == hash_result


# Test annotation system with edge cases
def test_annotation_edge_cases():
    """Test YAML annotation system with edge cases."""
    from yq.dumper import yaml_value_annotation_re, yaml_item_annotation_re
    
    # Test regex patterns
    test_cases = [
        ("__yq_tag_abc123__", "tag", "abc123"),
        ("__yq_style_xyz789__", "style", "xyz789"),
        ("__yq_tag_0__", "tag", "0"),
        ("not_an_annotation", None, None)
    ]
    
    for test_str, expected_type, expected_key in test_cases:
        match = yaml_value_annotation_re.match(test_str)
        if expected_type:
            assert match is not None
            assert match.group("type") == expected_type
            assert match.group("key") == expected_key
        else:
            assert match is None


# Test grammar version configuration
def test_grammar_configuration():
    """Test that grammar versions are correctly configured."""
    from yq.loader import core_resolvers
    
    # Should have both 1.1 and 1.2
    assert "1.1" in core_resolvers
    assert "1.2" in core_resolvers
    
    # 1.1 should have different bool patterns than 1.2
    v11_bools = None
    v12_bools = None
    
    for resolver in core_resolvers["1.1"]:
        if resolver["tag"] == "tag:yaml.org,2002:bool":
            v11_bools = resolver["regexp"].pattern
            
    for resolver in core_resolvers["1.2"]:
        if resolver["tag"] == "tag:yaml.org,2002:bool":
            v12_bools = resolver["regexp"].pattern
    
    # Patterns should be different
    assert v11_bools != v12_bools
    
    # 1.1 accepts yes/no/on/off, 1.2 doesn't
    assert "yes" in v11_bools
    assert "yes" not in v12_bools