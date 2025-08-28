#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/azure-mgmt-appconfiguration_env/lib/python3.13/site-packages/')

from hypothesis import given, strategies as st, assume, settings
import pytest
from azure.profiles import ProfileDefinition, DefaultProfile, KnownProfiles
from azure.profiles.multiapiclient import MultiApiClientMixin, InvalidMultiApiClientError


# Strategy for generating valid profile dictionaries
profile_dict_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=100).filter(lambda x: '.' in x),
    values=st.dictionaries(
        keys=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        values=st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=5
    ),
    min_size=0,
    max_size=10
)


@given(profile_dict=profile_dict_strategy, label=st.one_of(st.none(), st.text(min_size=0, max_size=100)))
def test_profile_definition_round_trip(profile_dict, label):
    """Test that ProfileDefinition.get_profile_dict() returns the same dict that was passed in."""
    profile = ProfileDefinition(profile_dict, label)
    
    # The get_profile_dict should return the exact same dictionary
    assert profile.get_profile_dict() == profile_dict
    
    # The label should be preserved
    assert profile.label == label
    
    # The repr should use label if available, else the dict repr
    if label:
        assert repr(profile) == label
    else:
        assert repr(profile) == repr(profile_dict)


@given(invalid_value=st.one_of(
    st.integers(),
    st.floats(),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text()),
    st.booleans(),
    st.none()
))
def test_default_profile_type_constraint(invalid_value):
    """Test that DefaultProfile.use() only accepts ProfileDefinition or KnownProfiles."""
    default_profile = DefaultProfile()
    
    # Should raise ValueError for non-ProfileDefinition/KnownProfiles values
    with pytest.raises(ValueError, match="Can only set as default a ProfileDefinition or a KnownProfiles"):
        default_profile.use(invalid_value)


@given(profile_name=st.text(min_size=1, max_size=100))
def test_known_profiles_from_name(profile_name):
    """Test KnownProfiles.from_name() behavior."""
    import re
    
    # Known valid profile names from the code
    valid_names = [
        "default", 
        "latest",
        "2017-03-09-profile",
        "2018-03-01-hybrid", 
        "2019-03-01-hybrid",
        "2020-09-01-hybrid"
    ]
    
    if profile_name in valid_names:
        # Should return a valid profile
        profile = KnownProfiles.from_name(profile_name)
        assert isinstance(profile, KnownProfiles)
        
        if profile_name == "default":
            assert profile is KnownProfiles.default
        elif profile_name == "latest":
            assert profile is KnownProfiles.latest
    else:
        # Should raise ValueError for unknown profile names
        # Need to escape regex special characters
        escaped_name = re.escape(profile_name)
        with pytest.raises(ValueError, match=f"No profile called {escaped_name}"):
            KnownProfiles.from_name(profile_name)


def test_known_profiles_use_restriction():
    """Test that only default profile allows use() method."""
    
    # Default profile should allow use()
    try:
        KnownProfiles.default.use(KnownProfiles.latest)
    except ValueError:
        pytest.fail("default profile should allow use()")
    
    # Non-default profiles should not allow use()
    non_default_profiles = [
        KnownProfiles.latest,
        KnownProfiles.v2017_03_09_profile,
        KnownProfiles.v2018_03_01_hybrid,
        KnownProfiles.v2019_03_01_hybrid,
        KnownProfiles.v2020_09_01_hybrid
    ]
    
    for profile in non_default_profiles:
        with pytest.raises(ValueError, match="use can only be used for `default` profile"):
            profile.use(KnownProfiles.latest)


def test_known_profiles_definition_restriction():
    """Test that only default profile allows definition() method."""
    
    # Default profile should allow definition()
    try:
        result = KnownProfiles.default.definition()
        assert result is not None
    except ValueError:
        pytest.fail("default profile should allow definition()")
    
    # Non-default profiles should not allow definition()
    non_default_profiles = [
        KnownProfiles.latest,
        KnownProfiles.v2017_03_09_profile,
        KnownProfiles.v2018_03_01_hybrid,
        KnownProfiles.v2019_03_01_hybrid,
        KnownProfiles.v2020_09_01_hybrid
    ]
    
    for profile in non_default_profiles:
        with pytest.raises(ValueError, match="use can only be used for `default` profile"):
            profile.definition()


class TestClient(MultiApiClientMixin):
    """Test client to verify MultiApiClientMixin behavior."""
    LATEST_PROFILE = ProfileDefinition({"TestClient": {None: "2021-01-01"}}, "test-latest")
    _PROFILE_TAG = "TestClient"


@given(api_version=st.text(min_size=1, max_size=20))
def test_multiapi_client_parameter_conflict(api_version):
    """Test that MultiApiClientMixin raises error when both api_version and profile are provided."""
    
    # Using both api_version and a non-default profile should raise ValueError
    with pytest.raises(ValueError, match="Cannot use api-version and profile parameters at the same time"):
        TestClient(api_version=api_version, profile=KnownProfiles.latest)
    
    # api_version with default profile should work (default is special case)
    try:
        client = TestClient(api_version=api_version, profile=KnownProfiles.default)
    except ValueError as e:
        if "Cannot use api-version and profile parameters" in str(e):
            pytest.fail("Should allow api_version with default profile")


def test_multiapi_client_missing_attributes():
    """Test that MultiApiClientMixin requires LATEST_PROFILE and _PROFILE_TAG."""
    
    # Missing LATEST_PROFILE
    class BadClient1(MultiApiClientMixin):
        _PROFILE_TAG = "BadClient1"
    
    with pytest.raises(InvalidMultiApiClientError, match="main client MUST define LATEST_PROFILE"):
        BadClient1()
    
    # Missing _PROFILE_TAG
    class BadClient2(MultiApiClientMixin):
        LATEST_PROFILE = ProfileDefinition({}, "bad")
    
    with pytest.raises(InvalidMultiApiClientError, match="main client MUST define _PROFILE_TAG"):
        BadClient2()


@given(
    profile_dict=st.dictionaries(
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
def test_multiapi_get_api_version(profile_dict):
    """Test _get_api_version method retrieves correct API versions."""
    
    # Ensure TestClient tag is in the dict
    if "TestClient" not in profile_dict:
        profile_dict["TestClient"] = {None: "2021-01-01"}
    
    # Create a profile and client
    profile = ProfileDefinition(profile_dict, "test-profile")
    client = TestClient(profile=profile)
    
    # Test retrieving API versions
    test_profile = profile_dict["TestClient"]
    
    for operation_group, expected_version in test_profile.items():
        if operation_group is None:
            # Test with an operation group not explicitly defined (should use default)
            actual_version = client._get_api_version("undefined_operation")
            assert actual_version == expected_version
        else:
            # Test with explicitly defined operation group
            actual_version = client._get_api_version(operation_group)
            assert actual_version == expected_version
    
    # Test that missing operation group with no default raises error
    if None not in test_profile:
        profile_dict_no_default = {"TestClient": {"specific_op": "2021-01-01"}}
        profile_no_default = ProfileDefinition(profile_dict_no_default, "no-default")
        client_no_default = TestClient(profile=profile_no_default)
        
        with pytest.raises(ValueError, match="does not contain a default API version"):
            client_no_default._get_api_version("undefined_operation")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])