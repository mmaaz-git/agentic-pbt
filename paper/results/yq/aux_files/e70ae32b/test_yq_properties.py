"""Property-based tests for yq module using Hypothesis."""

import sys
import json
import io
from datetime import datetime, date, time
from hashlib import sha224
from base64 import b64encode

# Add yq to path
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import yq
from hypothesis import given, strategies as st, assume
import pytest


# Strategy for generating datetime objects
datetime_strategy = st.datetimes(
    min_value=datetime(1900, 1, 1),
    max_value=datetime(2100, 12, 31)
)

date_strategy = st.dates(
    min_value=date(1900, 1, 1),
    max_value=date(2100, 12, 31)
)

time_strategy = st.times()


# Test 1: JSONDateTimeEncoder round-trip property
@given(dt=datetime_strategy)
def test_json_datetime_encoder_datetime_roundtrip(dt):
    """Test that datetime objects can be encoded to ISO format and decoded back."""
    encoder = yq.JSONDateTimeEncoder()
    encoded = encoder.encode(dt)
    
    # The encoded string should be valid JSON
    decoded = json.loads(encoded)
    
    # Should be in ISO format
    assert isinstance(decoded, str)
    
    # Should be able to parse it back
    parsed = datetime.fromisoformat(decoded)
    
    # Microseconds might be truncated in isoformat, so compare with precision
    assert abs((parsed - dt).total_seconds()) < 0.001


@given(d=date_strategy)
def test_json_datetime_encoder_date_roundtrip(d):
    """Test that date objects can be encoded to ISO format."""
    encoder = yq.JSONDateTimeEncoder()
    encoded = encoder.encode(d)
    
    decoded = json.loads(encoded)
    assert isinstance(decoded, str)
    
    # Should be able to parse it back as a date
    parsed = date.fromisoformat(decoded)
    assert parsed == d


@given(t=time_strategy)
def test_json_datetime_encoder_time_roundtrip(t):
    """Test that time objects can be encoded to ISO format."""
    encoder = yq.JSONDateTimeEncoder()
    encoded = encoder.encode(t)
    
    decoded = json.loads(encoded)
    assert isinstance(decoded, str)
    
    # Should be able to parse it back as a time
    parsed = time.fromisoformat(decoded)
    
    # Microseconds might be truncated, so compare with precision
    if parsed != t:
        # Check if difference is just in microseconds
        assert parsed.replace(microsecond=0) == t.replace(microsecond=0)


# Test 2: decode_docs invariant - should decode all valid JSON documents
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
def test_decode_docs_preserves_all_documents(docs):
    """Test that decode_docs correctly extracts all JSON documents from a concatenated string."""
    # Create a concatenated JSON string with newline separators
    json_str = '\n'.join(json.dumps(doc) for doc in docs) + '\n'
    
    # Decode using yq's decode_docs
    decoder = json.JSONDecoder()
    decoded_docs = list(yq.decode_docs(json_str, decoder))
    
    # Should get back all the original documents
    assert len(decoded_docs) == len(docs)
    assert decoded_docs == docs


@given(
    docs=st.lists(
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(min_size=1),
            st.lists(st.integers()),
            st.dictionaries(st.text(min_size=1), st.integers())
        ),
        min_size=1,
        max_size=10
    )
)
def test_decode_docs_handles_mixed_types(docs):
    """Test decode_docs with various JSON types, not just objects."""
    json_str = ''.join(json.dumps(doc) for doc in docs)
    
    decoder = json.JSONDecoder()
    decoded_docs = list(yq.decode_docs(json_str, decoder))
    
    assert len(decoded_docs) == len(docs)
    assert decoded_docs == docs


# Test 3: hash_key determinism
@given(
    key=st.one_of(
        st.text(min_size=0, max_size=1000),
        st.binary(min_size=0, max_size=1000)
    )
)
def test_hash_key_determinism(key):
    """Test that hash_key produces deterministic output for the same input."""
    from yq.loader import hash_key
    
    # Hash the same key multiple times
    hash1 = hash_key(key)
    hash2 = hash_key(key)
    hash3 = hash_key(key)
    
    # All hashes should be identical
    assert hash1 == hash2 == hash3
    
    # Result should be a valid base64 string
    assert isinstance(hash1, str)
    # Base64 encoded SHA224 should be 38 characters (28 bytes * 4/3)
    assert len(hash1) == 38


@given(
    key1=st.text(min_size=1, max_size=100),
    key2=st.text(min_size=1, max_size=100)
)
def test_hash_key_different_inputs_different_hashes(key1, key2):
    """Test that different keys produce different hashes (with high probability)."""
    assume(key1 != key2)
    
    from yq.loader import hash_key
    
    hash1 = hash_key(key1)
    hash2 = hash_key(key2)
    
    # Different keys should produce different hashes
    # (collision probability is negligible for SHA224)
    assert hash1 != hash2


# Test 4: Grammar version validation
@given(
    grammar_version=st.text(min_size=1, max_size=10).filter(lambda x: x not in ["1.1", "1.2"])
)
def test_invalid_grammar_version_raises_exception(grammar_version):
    """Test that invalid grammar versions raise an exception."""
    from yq.loader import set_yaml_grammar, default_loader
    
    class TestResolver:
        yaml_implicit_resolvers = {}
    
    resolver = TestResolver()
    
    with pytest.raises(Exception) as exc_info:
        set_yaml_grammar(resolver, grammar_version=grammar_version)
    
    assert f"Unknown grammar version {grammar_version}" in str(exc_info.value)


@given(
    grammar_version=st.sampled_from(["1.1", "1.2"])
)
def test_valid_grammar_versions_accepted(grammar_version):
    """Test that valid grammar versions are accepted."""
    from yq.loader import set_yaml_grammar
    
    class TestResolver:
        yaml_implicit_resolvers = {}
    
    resolver = TestResolver()
    
    # Should not raise an exception
    set_yaml_grammar(resolver, grammar_version=grammar_version)
    
    # Should have populated resolvers
    assert len(resolver.yaml_implicit_resolvers) > 0


# Test 5: Test get_dumper with different parameters
@given(
    use_annotations=st.booleans(),
    indentless=st.booleans(),
    grammar_version=st.sampled_from(["1.1", "1.2"])
)
def test_get_dumper_returns_valid_dumper(use_annotations, indentless, grammar_version):
    """Test that get_dumper returns a valid dumper class."""
    from yq.dumper import get_dumper
    import yaml
    
    dumper_class = get_dumper(
        use_annotations=use_annotations,
        indentless=indentless,
        grammar_version=grammar_version
    )
    
    # Should be a subclass of SafeDumper
    assert issubclass(dumper_class, yaml.SafeDumper)
    
    # Should be able to dump a simple document
    test_data = {"key": "value", "number": 42}
    result = yaml.dump(test_data, Dumper=dumper_class)
    assert isinstance(result, str)
    assert "key" in result
    assert "value" in result


# Test 6: Test the interaction between loader and dumper
@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_categories=["Cc", "Cs"])),
        st.one_of(
            st.integers(min_value=-1000, max_value=1000),
            st.text(max_size=50, alphabet=st.characters(blacklist_categories=["Cc", "Cs"])),
            st.booleans(),
            st.none()
        ),
        min_size=1,
        max_size=10
    )
)
def test_yaml_round_trip_preserves_data(data):
    """Test that data survives a round trip through YAML."""
    import yaml
    from yq.loader import get_loader
    from yq.dumper import get_dumper
    
    # Get loader and dumper
    loader_class = get_loader(use_annotations=False, expand_aliases=True, expand_merge_keys=True)
    dumper_class = get_dumper(use_annotations=False, indentless=False, grammar_version="1.1")
    
    # Dump to YAML
    yaml_str = yaml.dump(data, Dumper=dumper_class)
    
    # Load back from YAML
    loaded_data = yaml.load(yaml_str, Loader=loader_class)
    
    # Should preserve the data
    assert loaded_data == data