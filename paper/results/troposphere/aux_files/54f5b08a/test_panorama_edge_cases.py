#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import troposphere.panorama as panorama
from troposphere import Tags
import json


@settings(max_examples=500)
@given(
    payload_data=st.one_of(
        st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=127)),  # ASCII
        st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),  # Unicode without control chars
        st.text().map(lambda s: json.dumps({"nested": s})),  # JSON strings
        st.just(""),  # Empty string
        st.just(" " * 100),  # Whitespace
        st.just("\n\t\r"),  # Special whitespace
        st.text().filter(lambda s: "\x00" not in s)  # Exclude null bytes
    )
)
def test_manifest_payload_special_characters(payload_data):
    """Test ManifestPayload with special characters and edge cases"""
    
    payload = panorama.ManifestPayload(PayloadData=payload_data)
    dict_repr = payload.to_dict()
    
    # The payload data should be preserved exactly
    assert dict_repr['PayloadData'] == payload_data
    
    # Round trip should work
    reconstructed = panorama.ManifestPayload.from_dict(None, dict_repr)
    assert reconstructed.to_dict() == dict_repr


@settings(max_examples=500)
@given(
    tags_dict=st.dictionaries(
        keys=st.one_of(
            st.just(""),  # Empty key
            st.text(min_size=1, max_size=500),  # Very long keys
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),  # Unicode
            st.text().map(lambda s: "aws:" + s),  # Reserved prefix
            st.text().filter(lambda s: s and not s.isspace())  # Non-empty, non-whitespace
        ),
        values=st.one_of(
            st.just(""),  # Empty value
            st.text(min_size=0, max_size=1000),  # Long values
            st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),  # Unicode
            st.none(),  # None values
            st.text().map(json.dumps)  # JSON strings as values
        ),
        min_size=0,
        max_size=100
    )
)
def test_tags_edge_cases(tags_dict):
    """Test Tags with various edge cases"""
    
    # Filter out None values as Tags might not accept them
    filtered_dict = {k: v for k, v in tags_dict.items() if v is not None}
    
    if not filtered_dict:
        # Test empty tags
        tags = Tags({})
        assert tags.to_dict() == []
        return
    
    tags = Tags(filtered_dict)
    dict_repr = tags.to_dict()
    
    # Should be a list of key-value pairs
    assert isinstance(dict_repr, list)
    assert len(dict_repr) == len(filtered_dict)
    
    # All keys and values should be preserved
    result_dict = {item['Key']: item['Value'] for item in dict_repr}
    assert result_dict == filtered_dict


@settings(max_examples=500)
@given(
    extra_props=st.dictionaries(
        keys=st.text(min_size=1, max_size=50).filter(lambda s: s not in [
            'PackageName', 'StorageLocation', 'Tags'
        ]),
        values=st.one_of(
            st.text(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.none()
        ),
        min_size=0,
        max_size=10
    ),
    package_name=st.text(min_size=1, max_size=255)
)
def test_unexpected_properties(extra_props, package_name):
    """Test how objects handle unexpected properties"""
    
    # Try to create Package with extra properties
    kwargs = {'PackageName': package_name}
    kwargs.update(extra_props)
    
    try:
        pkg = panorama.Package("TestPkg", **kwargs)
        # The object should accept the properties in __init__
        # but may filter them out or raise errors later
        dict_repr = pkg.to_dict()
        
        # Check that only valid properties are in the output
        props = dict_repr['Properties']
        assert 'PackageName' in props
        
        # Extra properties might be ignored or included depending on implementation
        # Let's check what happens
        for key in extra_props:
            # If the property is in the output, it was accepted
            # If not, it was filtered out (which is also valid behavior)
            pass
            
    except (TypeError, ValueError) as e:
        # It's also valid to reject unexpected properties
        pass


@settings(max_examples=500)
@given(
    device=st.text(min_size=0, max_size=10000),
    manifest_data=st.text(min_size=0, max_size=10000),
    override_data=st.text(min_size=0, max_size=10000)
)
def test_large_payload_data(device, manifest_data, override_data):
    """Test with very large payload data"""
    
    app = panorama.ApplicationInstance(
        "LargeApp",
        DefaultRuntimeContextDevice=device,
        ManifestPayload=panorama.ManifestPayload(PayloadData=manifest_data),
        ManifestOverridesPayload=panorama.ManifestOverridesPayload(PayloadData=override_data)
    )
    
    dict_repr = app.to_dict()
    props = dict_repr['Properties']
    
    # All data should be preserved exactly
    assert props['DefaultRuntimeContextDevice'] == device
    assert props['ManifestPayload']['PayloadData'] == manifest_data
    assert props['ManifestOverridesPayload']['PayloadData'] == override_data
    
    # Round trip should work
    reconstructed = panorama.ApplicationInstance.from_dict("LargeApp2", props)
    assert reconstructed.to_dict()['Properties'] == props


@settings(max_examples=200)
@given(
    title=st.one_of(
        st.none(),
        st.just(""),
        st.text(min_size=1, max_size=255),
        st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        st.text().filter(lambda s: s and not s.isspace())
    )
)
def test_title_validation(title):
    """Test how objects handle various title values"""
    
    # Some titles might be invalid
    try:
        pkg = panorama.Package(
            title,
            PackageName="test-package"
        )
        dict_repr = pkg.to_dict()
        
        # If it succeeded, the title was valid
        # Check that it doesn't appear in the dict output
        assert 'title' not in dict_repr  # title is metadata, not a property
        assert title == pkg.title or (title is None and pkg.title is None)
        
    except (ValueError, TypeError) as e:
        # Some titles might be rejected
        # This is valid behavior for invalid titles
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])