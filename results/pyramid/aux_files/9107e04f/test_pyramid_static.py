"""Property-based tests for pyramid.static module using Hypothesis."""

import json
import mimetypes
import os
import sys
from unittest.mock import Mock

import pytest
from hypothesis import assume, given, settings, strategies as st

# Add the pyramid environment to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.static import (
    _secure_path,
    _compile_content_encodings,
    _add_vary,
    ManifestCacheBuster,
    QueryStringConstantCacheBuster,
)


# Test 1: _secure_path security properties
@given(st.lists(st.text()))
def test_secure_path_insecure_elements(path_tuple):
    """_secure_path should return None for paths containing '..' or '.' or empty string."""
    result = _secure_path(tuple(path_tuple))
    
    # If any element is '..', '.', or empty string, result should be None
    if any(elem in ['..', '.', ''] for elem in path_tuple):
        assert result is None, f"Expected None for insecure path {path_tuple}"
    # If any element contains '/', os.sep, or '\x00', result should be None
    elif any('/' in elem or os.sep in elem or '\x00' in elem for elem in path_tuple):
        assert result is None, f"Expected None for path with invalid chars {path_tuple}"
    else:
        # Otherwise, it should return a string
        assert result is not None
        assert isinstance(result, str)
        # The result should be the elements joined by '/'
        assert result == '/'.join(path_tuple)


# Test 2: _compile_content_encodings mapping properties
@given(st.lists(st.sampled_from(list(set(mimetypes.encodings_map.values())))))
def test_compile_content_encodings_properties(encodings):
    """Test that _compile_content_encodings creates correct mapping."""
    result = _compile_content_encodings(encodings)
    
    # Property 1: All keys in result should be from the input encodings
    assert all(key in encodings for key in result.keys()), \
        f"Result contains encoding not in input: {set(result.keys()) - set(encodings)}"
    
    # Property 2: All values should be lists of file extensions
    for encoding, extensions in result.items():
        assert isinstance(extensions, list)
        for ext in extensions:
            # Each extension should map to this encoding in mimetypes.encodings_map
            assert mimetypes.encodings_map.get(ext) == encoding, \
                f"Extension {ext} doesn't map to {encoding} in mimetypes.encodings_map"


# Test 3: _add_vary duplicate prevention
@given(
    st.lists(st.text(min_size=1, alphabet=st.characters(min_codepoint=65, max_codepoint=122))),
    st.text(min_size=1, alphabet=st.characters(min_codepoint=65, max_codepoint=122))
)
def test_add_vary_no_duplicates(existing_vary, new_option):
    """_add_vary should not add duplicate Vary headers (case-insensitive)."""
    response = Mock()
    response.vary = existing_vary.copy() if existing_vary else []
    
    _add_vary(response, new_option)
    
    # Check that no duplicates exist (case-insensitive)
    vary_lower = [v.lower() for v in response.vary]
    assert len(vary_lower) == len(set(vary_lower)), \
        f"Duplicate vary headers found: {response.vary}"
    
    # If new_option was already present (case-insensitive), count shouldn't change
    if any(v.lower() == new_option.lower() for v in existing_vary):
        assert len(response.vary) == len(existing_vary)
    else:
        assert len(response.vary) == len(existing_vary) + 1
        assert new_option in response.vary


# Test 4: ManifestCacheBuster.parse_manifest round-trip
@given(st.dictionaries(
    st.text(min_size=1, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
    st.text(min_size=1, alphabet=st.characters(blacklist_categories=('Cc', 'Cs')))
))
def test_manifest_parse_round_trip(manifest_dict):
    """parse_manifest should correctly parse JSON-encoded dictionaries."""
    # Skip if the dictionary would create invalid JSON
    try:
        json_bytes = json.dumps(manifest_dict).encode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError, TypeError):
        assume(False)
    
    buster = ManifestCacheBuster.__new__(ManifestCacheBuster)
    
    # Parse the JSON bytes
    result = buster.parse_manifest(json_bytes)
    
    # Should get back the same dictionary
    assert result == manifest_dict, \
        f"Round-trip failed: {manifest_dict} != {result}"


# Test 5: QueryStringConstantCacheBuster.tokenize invariant
@given(
    st.text(),  # token
    st.text(),  # param
    st.builds(Mock),  # request
    st.text(),  # subpath
    st.dictionaries(st.text(), st.text())  # kw
)
def test_query_string_constant_tokenize_invariant(token, param, request, subpath, kw):
    """QueryStringConstantCacheBuster.tokenize should always return the same token."""
    assume(param)  # param should not be empty
    
    buster = QueryStringConstantCacheBuster(token, param)
    
    # tokenize should always return the same token regardless of inputs
    result1 = buster.tokenize(request, subpath, kw)
    result2 = buster.tokenize(Mock(), "different", {"other": "data"})
    
    assert result1 == token
    assert result2 == token
    assert result1 == result2