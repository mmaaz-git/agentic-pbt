#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import troposphere.panorama as panorama

# Run tests with more examples
@settings(max_examples=1000)
@given(
    payload_data=st.text(min_size=0, max_size=10000),
    include_none=st.booleans()
)
def test_manifest_payload_intensive(payload_data, include_none):
    """Intensive test for ManifestPayload edge cases"""
    
    if include_none:
        # Test with no PayloadData
        obj = panorama.ManifestPayload()
        dict_repr = obj.to_dict()
        reconstructed = panorama.ManifestPayload.from_dict(None, dict_repr)
        assert reconstructed.to_dict() == dict_repr
    else:
        obj = panorama.ManifestPayload(PayloadData=payload_data)
        dict_repr = obj.to_dict()
        
        # Test that the payload data is preserved exactly
        assert 'PayloadData' in dict_repr
        assert dict_repr['PayloadData'] == payload_data
        
        reconstructed = panorama.ManifestPayload.from_dict(None, dict_repr)
        assert reconstructed.to_dict() == dict_repr


@settings(max_examples=1000)
@given(
    bool_input=st.one_of(
        st.just(True), st.just(False),
        st.just(1), st.just(0),
        st.just("true"), st.just("false"),
        st.just("True"), st.just("False"),
        st.just("1"), st.just("0"),
        st.just(2), st.just(-1),  # Invalid numeric values
        st.text(min_size=1, max_size=20)  # Random text
    )
)
def test_boolean_validator_edge_cases(bool_input):
    """Test boolean validator with various edge cases"""
    from troposphere.validators import boolean
    
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    if bool_input in valid_true:
        assert boolean(bool_input) is True
    elif bool_input in valid_false:
        assert boolean(bool_input) is False
    else:
        # Should raise ValueError for invalid inputs
        try:
            result = boolean(bool_input)
            assert False, f"Expected ValueError for {repr(bool_input)}, got {result}"
        except ValueError:
            pass  # Expected


@settings(max_examples=500)
@given(
    package_id=st.text(min_size=1, max_size=1000),
    package_version=st.text(min_size=1, max_size=100),
    patch_version=st.text(min_size=1, max_size=100),
    mark_latest=st.one_of(
        st.sampled_from([True, False, 1, 0, "true", "false", "True", "False", "1", "0"]),
        st.none()
    ),
    owner_account=st.one_of(st.none(), st.text(min_size=12, max_size=12).filter(str.isdigit)),
    updated_patch=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_package_version_all_properties(package_id, package_version, patch_version, 
                                       mark_latest, owner_account, updated_patch):
    """Test PackageVersion with all possible property combinations"""
    
    kwargs = {
        'PackageId': package_id,
        'PackageVersion': package_version,
        'PatchVersion': patch_version
    }
    
    if mark_latest is not None:
        kwargs['MarkLatest'] = mark_latest
    if owner_account is not None:
        kwargs['OwnerAccount'] = owner_account
    if updated_patch is not None:
        kwargs['UpdatedLatestPatchVersion'] = updated_patch
    
    pkg = panorama.PackageVersion("TestVersion", **kwargs)
    dict_repr = pkg.to_dict()
    
    # Check all required properties are present
    props = dict_repr['Properties']
    assert props['PackageId'] == package_id
    assert props['PackageVersion'] == package_version
    assert props['PatchVersion'] == patch_version
    
    # Check optional properties
    if mark_latest is not None:
        from troposphere.validators import boolean
        assert props['MarkLatest'] == boolean(mark_latest)
    if owner_account is not None:
        assert props['OwnerAccount'] == owner_account
    if updated_patch is not None:
        assert props['UpdatedLatestPatchVersion'] == updated_patch


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])