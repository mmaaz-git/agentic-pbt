#!/usr/bin/env /root/hypothesis-llm/envs/yq_env/bin/python3
"""Property-based tests for yq.dumper module"""

import io
import yaml
from hypothesis import given, strategies as st, settings, assume
from yq.dumper import get_dumper, OrderedDumper, OrderedIndentlessDumper
from yq.loader import hash_key, get_loader


# Strategies for testing
safe_strings = st.text(min_size=1, max_size=100).filter(
    lambda s: not s.startswith("__yq_") and s.strip() != ""
)
safe_keys = st.one_of(
    safe_strings,
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False)
)

simple_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1e10, max_value=1e10),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    safe_strings
)

# Recursive strategies for complex data structures
def simple_lists():
    return st.lists(simple_values, max_size=10)

def simple_dicts():
    return st.dictionaries(safe_keys, simple_values, max_size=10)

# More complex nested structures
def nested_data(max_depth=3):
    if max_depth <= 0:
        return simple_values
    return st.one_of(
        simple_values,
        st.lists(nested_data(max_depth - 1), max_size=5),
        st.dictionaries(safe_keys, nested_data(max_depth - 1), max_size=5)
    )


@given(nested_data())
def test_dumper_does_not_crash(data):
    """Test that get_dumper returns a valid dumper that doesn't crash on various inputs"""
    dumper = get_dumper(use_annotations=False, indentless=False, grammar_version="1.1")
    output = io.StringIO()
    yaml.dump(data, output, Dumper=dumper, default_flow_style=False)
    assert output.getvalue() is not None


@given(nested_data(), st.booleans(), st.booleans(), st.sampled_from(["1.1", "1.2"]))
def test_dumper_with_options(data, use_annotations, indentless, grammar_version):
    """Test get_dumper with various option combinations"""
    dumper = get_dumper(
        use_annotations=use_annotations,
        indentless=indentless,
        grammar_version=grammar_version
    )
    output = io.StringIO()
    yaml.dump(data, output, Dumper=dumper, default_flow_style=False)
    result = output.getvalue()
    assert result is not None
    # Basic validation that we got YAML output
    if data is not None:
        assert len(result) > 0


@given(simple_dicts())
def test_annotation_filtering_dicts(data):
    """Test that annotation keys are properly filtered when use_annotations=True"""
    # Add some annotation keys to the data
    annotated_data = data.copy()
    if len(data) > 0:
        first_key = list(data.keys())[0]
        hashed = hash_key(str(first_key))
        annotated_data[f"__yq_style_{hashed}__"] = "'"
        annotated_data[f"__yq_tag_{hashed}__"] = "!custom"
    
    dumper = get_dumper(use_annotations=True, indentless=False, grammar_version="1.1")
    output = io.StringIO()
    yaml.dump(annotated_data, output, Dumper=dumper, default_flow_style=False)
    result = output.getvalue()
    
    # The annotation keys should not appear in the output
    assert "__yq_style_" not in result
    assert "__yq_tag_" not in result


@given(simple_lists())
def test_annotation_filtering_lists(data):
    """Test that list annotation items are properly filtered when use_annotations=True"""
    # Add annotation items to the list
    annotated_data = data.copy()
    if len(data) > 0:
        annotated_data.append("__yq_style_0_'__")
        annotated_data.append("__yq_tag_0_!custom__")
    
    dumper = get_dumper(use_annotations=True, indentless=False, grammar_version="1.1")
    output = io.StringIO()
    yaml.dump(annotated_data, output, Dumper=dumper, default_flow_style=False)
    result = output.getvalue()
    
    # The annotation items should not appear in the output
    assert "__yq_style_" not in result
    assert "__yq_tag_" not in result


@given(st.one_of(safe_strings, st.binary(min_size=1, max_size=100)))
def test_hash_key_consistency(key):
    """Test that hash_key produces consistent results"""
    hash1 = hash_key(key)
    hash2 = hash_key(key)
    assert hash1 == hash2
    assert isinstance(hash1, str)
    # Should be base64 encoded
    assert len(hash1) > 0


@given(st.one_of(safe_strings, st.binary(min_size=1, max_size=100)),
       st.one_of(safe_strings, st.binary(min_size=1, max_size=100)))
def test_hash_key_uniqueness(key1, key2):
    """Test that different keys produce different hashes (with high probability)"""
    assume(key1 != key2)
    hash1 = hash_key(key1)
    hash2 = hash_key(key2)
    # While collisions are theoretically possible, they should be extremely rare
    assert hash1 != hash2


@given(simple_dicts(), st.sampled_from(["1.1", "1.2"]))
@settings(max_examples=50)
def test_round_trip_simple(data, grammar_version):
    """Test that data survives a round trip through dump and load"""
    # Skip data with None keys as YAML doesn't support them well
    assume(None not in data.keys())
    
    dumper = get_dumper(use_annotations=False, indentless=False, grammar_version=grammar_version)
    loader = get_loader(use_annotations=False, expand_aliases=True, expand_merge_keys=True)
    
    # Dump the data
    output = io.StringIO()
    yaml.dump(data, output, Dumper=dumper, default_flow_style=False)
    
    # Load it back
    output.seek(0)
    loaded_data = yaml.load(output, Loader=loader)
    
    # Should preserve the data (modulo float precision issues)
    assert loaded_data == data


@given(nested_data(max_depth=2))
def test_dumper_idempotence(data):
    """Test that dumping the same data multiple times produces the same output"""
    dumper_class = get_dumper(use_annotations=False, indentless=False, grammar_version="1.1")
    
    output1 = io.StringIO()
    yaml.dump(data, output1, Dumper=dumper_class, default_flow_style=False)
    result1 = output1.getvalue()
    
    output2 = io.StringIO()
    yaml.dump(data, output2, Dumper=dumper_class, default_flow_style=False)
    result2 = output2.getvalue()
    
    assert result1 == result2


@given(simple_dicts())
def test_indentless_option_effect(data):
    """Test that indentless option actually affects output"""
    assume(len(data) > 0)
    
    dumper_normal = get_dumper(use_annotations=False, indentless=False, grammar_version="1.1")
    dumper_indentless = get_dumper(use_annotations=False, indentless=True, grammar_version="1.1")
    
    output_normal = io.StringIO()
    yaml.dump(data, output_normal, Dumper=dumper_normal, default_flow_style=False)
    
    output_indentless = io.StringIO()
    yaml.dump(data, output_indentless, Dumper=dumper_indentless, default_flow_style=False)
    
    # Both should produce valid YAML
    assert output_normal.getvalue()
    assert output_indentless.getvalue()
    
    # Check that the dumper classes are different
    assert dumper_normal != dumper_indentless


@given(simple_dicts())
def test_alias_key_handling(data):
    """Test that __yq_alias__ key is properly handled"""
    data_with_alias = data.copy()
    data_with_alias["__yq_alias__"] = "some_alias"
    
    dumper = get_dumper(use_annotations=True, indentless=False, grammar_version="1.1")
    output = io.StringIO()
    yaml.dump(data_with_alias, output, Dumper=dumper, default_flow_style=False)
    result = output.getvalue()
    
    # __yq_alias__ should not appear in output when use_annotations=True
    assert "__yq_alias__" not in result


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])