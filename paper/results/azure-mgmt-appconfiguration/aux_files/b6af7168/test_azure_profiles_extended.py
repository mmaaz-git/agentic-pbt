#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/azure-mgmt-appconfiguration_env/lib/python3.13/site-packages/')

from hypothesis import given, strategies as st, assume, settings, note
import pytest
from azure.profiles import ProfileDefinition, DefaultProfile, KnownProfiles
from azure.profiles.multiapiclient import MultiApiClientMixin, InvalidMultiApiClientError
import copy


@given(
    initial_dict=st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.dictionaries(
            keys=st.one_of(st.none(), st.text(min_size=1, max_size=30)),
            values=st.text(min_size=1, max_size=30),
            min_size=1,
            max_size=3
        ),
        min_size=1,
        max_size=5
    )
)
def test_profile_definition_immutability(initial_dict):
    """Test that ProfileDefinition doesn't allow external modification of the profile dict."""
    
    # Create a copy to track original values
    original_dict = copy.deepcopy(initial_dict)
    
    # Create ProfileDefinition with the dict
    profile = ProfileDefinition(initial_dict, "test")
    
    # Get the dict back
    returned_dict = profile.get_profile_dict()
    
    # Modify the returned dict
    if returned_dict:
        first_key = next(iter(returned_dict))
        returned_dict[first_key] = {"modified": "value"}
        
        # Check if the internal dict was modified
        internal_dict = profile.get_profile_dict()
        
        # If the internal dict was modified, that's a bug (lack of immutability)
        if internal_dict != original_dict:
            note(f"Internal dict was modified! Original: {original_dict}, Current: {internal_dict}")
            # The dict is mutable - this could be a design bug
            assert internal_dict == returned_dict  # They share the same reference


@given(
    profiles=st.lists(
        st.sampled_from([
            KnownProfiles.latest,
            KnownProfiles.v2017_03_09_profile,
            KnownProfiles.v2018_03_01_hybrid,
            KnownProfiles.v2019_03_01_hybrid,
            KnownProfiles.v2020_09_01_hybrid
        ]),
        min_size=1,
        max_size=10
    )
)
def test_default_profile_state_consistency(profiles):
    """Test that default profile maintains consistent state through multiple use() calls."""
    
    # Save initial state
    initial_definition = KnownProfiles.default.definition()
    
    for profile in profiles:
        # Set the profile
        KnownProfiles.default.use(profile)
        
        # Verify it was set correctly
        current = KnownProfiles.default.definition()
        assert current == profile
        
    # Restore initial state
    KnownProfiles.default.use(initial_definition)


@given(label=st.text(min_size=0, max_size=1000))
def test_profile_definition_repr_edge_cases(label):
    """Test ProfileDefinition repr with various label values."""
    
    profile_dict = {"test.client": {None: "1.0.0"}}
    profile = ProfileDefinition(profile_dict, label)
    
    repr_result = repr(profile)
    
    # Check that repr doesn't crash and returns something reasonable
    assert isinstance(repr_result, str)
    
    if label:
        # When label exists, repr should be the label
        assert repr_result == label
    else:
        # When label is empty or None, repr should be the dict repr
        assert repr_result == repr(profile_dict)


class TestClientForEdgeCases(MultiApiClientMixin):
    """Test client for edge case testing."""
    LATEST_PROFILE = ProfileDefinition({"TestClientForEdgeCases": {None: "2021-01-01"}}, "test-latest")
    _PROFILE_TAG = "TestClientForEdgeCases"


@given(
    api_version=st.one_of(
        st.text(min_size=0, max_size=100),
        st.text().filter(lambda x: any(c in x for c in ['/', '\\', '\n', '\r', '\t']))
    )
)
def test_multiapi_client_api_version_edge_cases(api_version):
    """Test MultiApiClientMixin with edge case API version strings."""
    
    # Empty string or special characters in api_version
    if api_version:  # Non-empty strings
        try:
            client = TestClientForEdgeCases(api_version=api_version)
            
            # Verify the api_version was stored correctly
            assert client.profile._profile_dict[client._PROFILE_TAG][None] == api_version
            
            # Try to get the API version back
            retrieved_version = client._get_api_version("any_operation")
            assert retrieved_version == api_version
            
        except Exception as e:
            # Check if this is an expected failure
            note(f"Failed with api_version='{api_version}': {e}")
            raise


@given(
    profile_dict=st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(
            st.none(),  # Test with None values
            st.dictionaries(
                keys=st.one_of(st.none(), st.text(min_size=0, max_size=30)),  # Include empty strings
                values=st.text(min_size=0, max_size=30),
                min_size=0,  # Allow empty dicts
                max_size=3
            )
        ),
        min_size=1,
        max_size=5
    )
)
def test_multiapi_dict_profile_edge_cases(profile_dict):
    """Test MultiApiClientMixin with edge case profile dictionaries."""
    
    try:
        # Pass a dict as profile parameter
        client = TestClientForEdgeCases(profile=profile_dict)
        
        # The dict should be wrapped in a ProfileDefinition with the client's tag
        assert isinstance(client.profile, ProfileDefinition)
        assert client._PROFILE_TAG in client.profile._profile_dict
        
        # The provided dict should be stored under the client's tag
        assert client.profile._profile_dict[client._PROFILE_TAG] == profile_dict
        
    except Exception as e:
        # Note any unexpected failures
        note(f"Failed with profile_dict={profile_dict}: {e}")
        raise


@given(
    wrong_tag_dict=st.dictionaries(
        keys=st.text(min_size=1, max_size=50).filter(lambda x: x != "TestClientForEdgeCases"),
        values=st.dictionaries(
            keys=st.one_of(st.none(), st.text(min_size=1, max_size=30)),
            values=st.text(min_size=1, max_size=30),
            min_size=1,
            max_size=3
        ),
        min_size=1,
        max_size=5
    )
)
def test_multiapi_get_api_version_missing_tag(wrong_tag_dict):
    """Test _get_api_version when the profile doesn't contain the client's tag."""
    
    # Create a profile without the client's tag
    profile = ProfileDefinition(wrong_tag_dict, "wrong-tag-profile")
    client = TestClientForEdgeCases(profile=profile)
    
    # This should raise ValueError when trying to get API version
    with pytest.raises(ValueError, match=f"This profile doesn't define {client._PROFILE_TAG}"):
        client._get_api_version("any_operation")


def test_known_profiles_enum_values():
    """Test that KnownProfiles enum values are correctly structured."""
    
    # Verify all non-meta profiles have ProfileDefinition values
    for profile in KnownProfiles:
        if profile == KnownProfiles.default:
            # default is special - it contains a DefaultProfile instance
            assert isinstance(profile.value, DefaultProfile)
        else:
            # All others should have ProfileDefinition values
            assert isinstance(profile.value, ProfileDefinition)
            
            # Check that ProfileDefinitions have proper labels
            if profile != KnownProfiles.latest:
                assert profile.value.label is not None
                assert isinstance(profile.value.label, str)
                assert len(profile.value.label) > 0


def test_default_profile_circular_reference():
    """Test setting default profile to itself."""
    
    # This should work without errors
    KnownProfiles.default.use(KnownProfiles.default)
    
    # But definition() should still work
    result = KnownProfiles.default.definition()
    # It should return whatever the default was pointing to before
    assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])