"""Property-based tests for Django utility functions using Hypothesis."""

import math
from hypothesis import assume, given, strategies as st, settings
import django.utils.text
import django.utils.encoding


# Test 1: IRI/URI round-trip property
@given(st.text())
def test_iri_uri_round_trip(text):
    """Test that IRI to URI conversion preserves information for valid IRIs."""
    # Skip None and empty strings
    assume(text)
    
    # Convert IRI to URI and back
    uri = django.utils.encoding.iri_to_uri(text)
    iri_back = django.utils.encoding.uri_to_iri(uri)
    
    # The round-trip might normalize the encoding but should preserve the content
    # Let's test that converting again gives the same result (stability)
    uri2 = django.utils.encoding.iri_to_uri(iri_back)
    assert uri == uri2, f"IRI/URI conversion not stable: {repr(text)} -> {repr(uri)} != {repr(uri2)}"


# Test 2: slugify idempotence
@given(st.text())
def test_slugify_idempotent(text):
    """Test that slugify is idempotent - applying it twice gives same result as once."""
    slug_once = django.utils.text.slugify(text)
    slug_twice = django.utils.text.slugify(slug_once)
    assert slug_once == slug_twice, f"slugify not idempotent: {repr(text)} -> {repr(slug_once)} -> {repr(slug_twice)}"


# Test 3: slugify with unicode idempotence
@given(st.text())
def test_slugify_unicode_idempotent(text):
    """Test that slugify with allow_unicode=True is idempotent."""
    slug_once = django.utils.text.slugify(text, allow_unicode=True)
    slug_twice = django.utils.text.slugify(slug_once, allow_unicode=True)
    assert slug_once == slug_twice, f"slugify(allow_unicode=True) not idempotent: {repr(text)}"


# Test 4: normalize_newlines idempotence  
@given(st.text())
def test_normalize_newlines_idempotent(text):
    """Test that normalize_newlines is idempotent."""
    normalized_once = django.utils.text.normalize_newlines(text)
    normalized_twice = django.utils.text.normalize_newlines(normalized_once)
    assert normalized_once == normalized_twice, f"normalize_newlines not idempotent: {repr(text)}"


# Test 5: capfirst preserves length
@given(st.text(min_size=1))
def test_capfirst_preserves_length(text):
    """Test that capfirst preserves string length."""
    result = django.utils.text.capfirst(text)
    assert len(result) == len(text), f"capfirst changed length: {repr(text)} ({len(text)}) -> {repr(result)} ({len(result)})"


# Test 6: camel_case_to_spaces idempotence
@given(st.text())
def test_camel_case_to_spaces_idempotent(text):
    """Test that camel_case_to_spaces is idempotent."""
    converted_once = django.utils.text.camel_case_to_spaces(text)
    converted_twice = django.utils.text.camel_case_to_spaces(converted_once)
    assert converted_once == converted_twice, f"camel_case_to_spaces not idempotent: {repr(text)}"


# Test 7: compress_string and decompress round-trip
@given(st.binary())
def test_compress_decompress_round_trip(data):
    """Test that compress_string and decompression preserve data."""
    import gzip
    
    compressed = django.utils.text.compress_string(data)
    decompressed = gzip.decompress(compressed)
    assert data == decompressed, f"Compress/decompress failed for data of length {len(data)}"


# Test 8: get_valid_filename removes unsafe characters
@given(st.text(min_size=1))
def test_get_valid_filename_safe(text):
    """Test that get_valid_filename produces safe filenames."""
    filename = django.utils.text.get_valid_filename(text)
    # The result should not contain directory separators or null bytes
    assert '/' not in filename, f"get_valid_filename left '/' in: {repr(text)} -> {repr(filename)}"
    assert '\\' not in filename, f"get_valid_filename left '\\' in: {repr(text)} -> {repr(filename)}"
    assert '\x00' not in filename, f"get_valid_filename left null byte in: {repr(text)} -> {repr(filename)}"
    # Should not be empty unless input was all invalid chars
    if any(c.isalnum() or c in '-_' for c in text):
        assert filename, f"get_valid_filename returned empty for: {repr(text)}"


# Test 9: Multiple encoding/decoding functions preserve valid UTF-8
@given(st.text())
def test_force_str_bytes_round_trip(text):
    """Test that force_str and force_bytes preserve content."""
    # Convert to bytes and back
    as_bytes = django.utils.encoding.force_bytes(text)
    back_to_str = django.utils.encoding.force_str(as_bytes)
    assert text == back_to_str, f"force_bytes/force_str round trip failed: {repr(text)}"


# Test 10: escape_uri_path should be idempotent for already-escaped paths
@given(st.text())
def test_escape_uri_path_stability(text):
    """Test that escape_uri_path is stable when applied multiple times."""
    escaped_once = django.utils.encoding.escape_uri_path(text)
    escaped_twice = django.utils.encoding.escape_uri_path(escaped_once)
    # The second escape might differ if the first escape created sequences that get re-escaped
    # But a third application should equal the second (stability after initial escaping)
    escaped_thrice = django.utils.encoding.escape_uri_path(escaped_twice)
    assert escaped_twice == escaped_thrice, f"escape_uri_path not stable: {repr(text)}"