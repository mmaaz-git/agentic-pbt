#!/usr/bin/env python3
"""Property-based tests for troposphere.grafana module."""

import math
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, settings, strategies as st
import troposphere.grafana as grafana
from troposphere.validators import boolean, double
from troposphere import AWSObject, AWSProperty


# Test 1: Boolean validator edge cases
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator handles all documented valid inputs."""
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["true", "True", "false", "False", "0", "1"]),
    st.floats(allow_nan=True, allow_infinity=True),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator rejects invalid inputs."""
    try:
        result = boolean(value)
        # If we get here without exception, it's a bug
        assert False, f"boolean({value!r}) should have raised ValueError but returned {result!r}"
    except ValueError:
        pass  # Expected behavior
    except Exception as e:
        # Any other exception is a bug
        assert False, f"boolean({value!r}) raised unexpected {type(e).__name__}: {e}"


# Test 2: Double validator edge cases
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().map(str).filter(lambda s: s.replace('.', '', 1).replace('-', '', 1).replace('+', '', 1).replace('e', '', 1).replace('E', '', 1).isdigit() if s else False)
))
def test_double_validator_valid_inputs(value):
    """Test that double validator accepts valid numeric inputs."""
    try:
        # First check if Python can convert it to float
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            return  # Skip NaN and Inf values
    except (ValueError, TypeError, OverflowError):
        return  # Skip if Python can't convert it
    
    result = double(value)
    assert result == value  # Should return the original value


@given(st.one_of(
    st.text().filter(lambda x: not x.replace('.', '', 1).replace('-', '', 1).replace('+', '', 1).replace('e', '', 1).replace('E', '', 1).isdigit() if x else True),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.sampled_from([None, [], {}, set()])
))
def test_double_validator_invalid_inputs(value):
    """Test that double validator rejects non-numeric inputs."""
    # Skip values that might be valid
    try:
        float(value)
        return  # If it converts to float, skip this test case
    except (ValueError, TypeError):
        pass  # Expected - continue with test
    
    try:
        result = double(value)
        assert False, f"double({value!r}) should have raised ValueError but returned {result!r}"
    except ValueError:
        pass  # Expected behavior


# Test 3: Round-trip property for VpcConfiguration
@given(
    security_groups=st.lists(st.text(min_size=1, alphabet=st.characters(min_codepoint=65, max_codepoint=122)), min_size=1, max_size=5),
    subnet_ids=st.lists(st.text(min_size=1, alphabet=st.characters(min_codepoint=65, max_codepoint=122)), min_size=1, max_size=5)
)
def test_vpc_configuration_roundtrip(security_groups, subnet_ids):
    """Test that VpcConfiguration survives to_dict/from_dict round-trip."""
    # Create original object
    vpc_config = grafana.VpcConfiguration(
        SecurityGroupIds=security_groups,
        SubnetIds=subnet_ids
    )
    
    # Convert to dict
    vpc_dict = vpc_config.to_dict()
    
    # Create new object from dict
    vpc_config2 = grafana.VpcConfiguration._from_dict(**vpc_dict)
    
    # Compare
    assert vpc_config2.to_dict() == vpc_dict
    assert vpc_config2.SecurityGroupIds == security_groups
    assert vpc_config2.SubnetIds == subnet_ids


# Test 4: Required properties validation for Workspace
@given(
    account_access=st.sampled_from(["CURRENT_ACCOUNT", "ORGANIZATION"]),
    auth_providers=st.lists(st.sampled_from(["AWS_SSO", "SAML"]), min_size=1, max_size=2),
    permission_type=st.sampled_from(["SERVICE_MANAGED", "CUSTOMER_MANAGED"])
)
def test_workspace_required_properties(account_access, auth_providers, permission_type):
    """Test that Workspace validates required properties correctly."""
    # Create with all required properties - should work
    workspace = grafana.Workspace(
        title="TestWorkspace",
        AccountAccessType=account_access,
        AuthenticationProviders=auth_providers,
        PermissionType=permission_type
    )
    
    # Should be able to convert to dict
    workspace_dict = workspace.to_dict()
    assert workspace_dict is not None
    assert "Properties" in workspace_dict
    assert workspace_dict["Properties"]["AccountAccessType"] == account_access
    assert workspace_dict["Properties"]["AuthenticationProviders"] == auth_providers
    assert workspace_dict["Properties"]["PermissionType"] == permission_type


@given(
    auth_providers=st.lists(st.sampled_from(["AWS_SSO", "SAML"]), min_size=1, max_size=2),
    permission_type=st.sampled_from(["SERVICE_MANAGED", "CUSTOMER_MANAGED"])
)
def test_workspace_missing_required_property(auth_providers, permission_type):
    """Test that Workspace fails validation when required property is missing."""
    # Create without AccountAccessType (required)
    workspace = grafana.Workspace(
        title="TestWorkspace",
        AuthenticationProviders=auth_providers,
        PermissionType=permission_type
    )
    
    # Should raise ValueError when validating
    try:
        workspace.to_dict()  # This triggers validation
        assert False, "Should have raised ValueError for missing required property"
    except ValueError as e:
        assert "AccountAccessType" in str(e)


# Test 5: Property that tests invalid property names
@given(
    prop_name=st.text(min_size=1).filter(lambda x: x not in [
        "AccountAccessType", "AuthenticationProviders", "ClientToken", 
        "DataSources", "Description", "GrafanaVersion", "Name",
        "NetworkAccessControl", "NotificationDestinations", "OrganizationRoleName",
        "OrganizationalUnits", "PermissionType", "PluginAdminEnabled",
        "RoleArn", "SamlConfiguration", "StackSetName", "VpcConfiguration",
        # Also filter out special attributes
        "Condition", "CreationPolicy", "DeletionPolicy", "DependsOn",
        "Metadata", "UpdatePolicy", "UpdateReplacePolicy"
    ]),
    prop_value=st.text()
)
def test_workspace_invalid_property_name(prop_name, prop_value):
    """Test that Workspace rejects invalid property names."""
    # Create workspace with required properties
    workspace = grafana.Workspace(
        title="TestWorkspace",
        AccountAccessType="CURRENT_ACCOUNT",
        AuthenticationProviders=["AWS_SSO"],
        PermissionType="SERVICE_MANAGED"
    )
    
    # Try to set invalid property
    try:
        setattr(workspace, prop_name, prop_value)
        # Check if it was actually set in properties
        if hasattr(workspace, 'properties') and prop_name in workspace.properties:
            assert False, f"Invalid property {prop_name!r} was accepted"
    except AttributeError:
        pass  # Expected for invalid properties


# Test 6: Edge case for LoginValidityDuration in SamlConfiguration
@given(duration=st.floats(allow_nan=True, allow_infinity=True))
def test_saml_configuration_login_validity_duration_edge_cases(duration):
    """Test edge cases for LoginValidityDuration which uses double validator."""
    idp_metadata = grafana.IdpMetadata(Url="https://example.com/metadata")
    
    # Check if the duration is a valid double
    try:
        float_val = float(duration)
        is_valid_double = not (math.isnan(float_val) or math.isinf(float_val))
    except (ValueError, TypeError, OverflowError):
        is_valid_double = False
    
    try:
        saml_config = grafana.SamlConfiguration(
            IdpMetadata=idp_metadata,
            LoginValidityDuration=duration
        )
        
        # If we get here, the value was accepted
        if not is_valid_double:
            # NaN and Inf might be accepted - let's check
            saml_dict = saml_config.to_dict(validation=False)
            # The value should have been accepted
    except (ValueError, TypeError) as e:
        # Should only fail for invalid doubles
        if is_valid_double:
            assert False, f"Valid double {duration} was rejected: {e}"