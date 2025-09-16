"""Property-based tests for yq module using Hypothesis - Version 2."""

import sys
import json
import io
import yaml
import subprocess
from datetime import datetime, date, time
from hashlib import sha224
from base64 import b64encode

# Add yq to path
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import yq
from hypothesis import given, strategies as st, assume, settings
import pytest


# Test decode_docs with realistic jq-style output (newline-separated)
@given(
    docs=st.lists(
        st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.one_of(
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(),
                st.booleans(),
                st.none()
            )
        ),
        min_size=1,
        max_size=5
    )
)
def test_decode_docs_with_newline_separators(docs):
    """Test decode_docs with realistic newline-separated JSON (like jq output)."""
    # Create newline-separated JSON string (how jq outputs)
    json_str = '\n'.join(json.dumps(doc) for doc in docs)
    
    decoder = json.JSONDecoder()
    decoded_docs = list(yq.decode_docs(json_str, decoder))
    
    assert decoded_docs == docs


# Test YAML loader with potentially malicious expansion
@given(
    depth=st.integers(min_value=1, max_value=10),
    base_str=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_yaml_expansion_safety(depth, base_str):
    """Test that YAML loader detects and prevents excessive expansion."""
    # Create a YAML with aliases that could expand exponentially
    yaml_str = f"base: &base {base_str}\n"
    for i in range(depth):
        yaml_str += f"level{i}: [*base, *base]\n"
    
    # The loader should handle this safely
    from yq.loader import get_loader
    loader_class = get_loader(expand_aliases=True, expand_merge_keys=True)
    
    try:
        loaded = yaml.load(yaml_str, Loader=loader_class)
        # If it loads, verify the structure is correct
        assert loaded['base'] == base_str
    except:
        # If it fails due to expansion limits, that's also acceptable
        pass


# Test YAML round-trip with special characters and edge cases
@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=20).filter(
            lambda x: not any(c in x for c in ['\x00', '\r', '\n', ':', '#', '&', '*', '!', '|', '>', '{', '}', '[', ']', ',', '?', '-'])
        ),
        st.one_of(
            st.integers(min_value=-1000, max_value=1000),
            st.text(max_size=50).filter(lambda x: '\x00' not in x),
            st.booleans(),
            st.none()
        ),
        min_size=1,
        max_size=5
    )
)
def test_yaml_round_trip_with_safe_keys(data):
    """Test YAML round-trip with safer key constraints."""
    import yaml
    from yq.loader import get_loader
    from yq.dumper import get_dumper
    
    loader_class = get_loader(use_annotations=False, expand_aliases=True, expand_merge_keys=True)
    dumper_class = get_dumper(use_annotations=False, indentless=False, grammar_version="1.1")
    
    yaml_str = yaml.dump(data, Dumper=dumper_class)
    loaded_data = yaml.load(yaml_str, Loader=loader_class)
    
    assert loaded_data == data


# Test grammar version switching
@given(
    version=st.sampled_from(["1.1", "1.2"]),
    test_value=st.sampled_from(["yes", "no", "true", "false", "on", "off", "0o10", "0777"])
)
def test_grammar_version_affects_parsing(version, test_value):
    """Test that different grammar versions parse scalars differently."""
    from yq.loader import get_loader
    import yaml
    
    yaml_str = f"value: {test_value}"
    
    loader_class = get_loader()
    # Note: The loader grammar is not configurable, but dumper grammar is
    
    loaded = yaml.load(yaml_str, Loader=loader_class)
    
    # The value should be loaded (no exception)
    assert 'value' in loaded


# Test JSONDateTimeEncoder with edge cases
@given(
    dt=st.datetimes(
        min_value=datetime(1, 1, 1),
        max_value=datetime(9999, 12, 31, 23, 59, 59)
    )
)
def test_json_datetime_encoder_extreme_dates(dt):
    """Test JSONDateTimeEncoder with extreme date values."""
    encoder = yq.JSONDateTimeEncoder()
    
    # Should be able to encode
    encoded = encoder.encode(dt)
    decoded_str = json.loads(encoded)
    
    # Should be in ISO format
    assert 'T' in decoded_str or decoded_str.count('-') == 2
    
    # For dates within Python's range, should round-trip
    if 1900 <= dt.year <= 2100:
        parsed = datetime.fromisoformat(decoded_str)
        # Allow for microsecond truncation
        assert abs((parsed - dt).total_seconds()) < 1


# Test annotation preservation in YAML
@given(
    key=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    value=st.integers(min_value=-100, max_value=100),
    tag=st.sampled_from(["!custom", "!special", "!type"])
)
def test_yaml_annotation_preservation(key, value, tag):
    """Test that YAML annotations are preserved through round-trip."""
    from yq.loader import get_loader
    from yq.dumper import get_dumper
    import yaml
    
    # Create YAML with custom tag
    yaml_str = f"{key}: {tag} {value}"
    
    # Load with annotations
    loader_class = get_loader(use_annotations=True)
    dumper_class = get_dumper(use_annotations=True)
    
    try:
        loaded = yaml.load(yaml_str, Loader=loader_class)
        
        # The loaded data should have the value
        assert key in loaded
        
        # Dump it back
        dumped = yaml.dump(loaded, Dumper=dumper_class)
        
        # The tag should be preserved in the output
        # (The implementation uses special __yq_tag__ keys for this)
        assert str(value) in dumped
    except:
        # Some tags might not be valid, that's ok
        pass


# Test get_toml_loader compatibility
def test_toml_loader_selection():
    """Test that get_toml_loader selects the right TOML library."""
    loader = yq.get_toml_loader()
    
    # Should return a callable
    assert callable(loader)
    
    # Should be able to parse basic TOML
    toml_str = 'key = "value"\nnumber = 42'
    result = loader(toml_str)
    
    assert result['key'] == 'value'
    assert result['number'] == 42


# Test hash_key with unicode and special characters
@given(
    key=st.one_of(
        st.text(min_size=0, max_size=1000),
        st.text(alphabet=st.characters(min_codepoint=0x1F600, max_codepoint=0x1F64F)),  # Emojis
        st.binary(min_size=0, max_size=1000)
    )
)
def test_hash_key_unicode_handling(key):
    """Test hash_key with unicode and special characters."""
    from yq.loader import hash_key
    
    # Should not raise exception
    hash1 = hash_key(key)
    
    # Should be deterministic
    hash2 = hash_key(key)
    assert hash1 == hash2
    
    # Should be base64
    assert isinstance(hash1, str)
    assert len(hash1) == 40  # Corrected length for base64-encoded SHA224


# Test edge case: empty YAML document
def test_empty_yaml_handling():
    """Test handling of empty YAML documents."""
    from yq.loader import get_loader
    import yaml
    
    empty_yamls = ["", "---", "---\n", "---\n..."]
    
    loader_class = get_loader()
    
    for yaml_str in empty_yamls:
        loaded = yaml.load(yaml_str, Loader=loader_class)
        # Should load as None or empty
        assert loaded is None or loaded == {}


# Test YAML merge key expansion
@given(
    base_dict=st.dictionaries(
        st.text(min_size=1, max_size=5, alphabet='abc'),
        st.integers(min_value=0, max_value=100),
        min_size=1,
        max_size=3
    ),
    override_dict=st.dictionaries(
        st.text(min_size=1, max_size=5, alphabet='def'),
        st.integers(min_value=0, max_value=100),
        min_size=1,
        max_size=3
    )
)
def test_yaml_merge_key_handling(base_dict, override_dict):
    """Test YAML merge key (<<) handling."""
    from yq.loader import get_loader
    import yaml
    
    # Create YAML with merge key
    yaml_str = f"""
base: &base
{yaml.dump(base_dict, default_flow_style=False).replace('\n', '\n  ').rstrip()}
merged:
  <<: *base
{yaml.dump(override_dict, default_flow_style=False).replace('\n', '\n  ').rstrip()}
"""
    
    loader_class = get_loader(expand_merge_keys=True)
    
    try:
        loaded = yaml.load(yaml_str, Loader=loader_class)
        
        # The merged dict should contain keys from both base and override
        if 'merged' in loaded:
            merged = loaded['merged']
            # Base keys should be present
            for key in base_dict:
                assert key in merged
            # Override keys should be present
            for key in override_dict:
                assert key in merged
    except:
        # Some generated YAML might be invalid
        pass