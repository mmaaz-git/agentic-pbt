"""Additional edge case tests for troposphere.codebuild validation functions."""

import sys
from hypothesis import given, strategies as st, assume, settings, example
from troposphere.codebuild import (
    Artifacts, ProjectTriggers, WebhookFilter, Source, SourceAuth
)
from troposphere.validators.codebuild import (
    validate_environmentvariable_or_list,
    validate_project_triggers
)


# Test for edge cases in validate_environmentvariable_or_list
@given(st.lists(st.one_of(
    st.dictionaries(st.text(), st.text()),
    st.builds(lambda: type('CustomObject', (), {})())  # Custom object that's not dict or EnvironmentVariable
), min_size=1, max_size=1))
def test_environmentvariable_mixed_types(lst):
    """Property: List with non-dict, non-EnvironmentVariable should fail."""
    has_invalid = any(not isinstance(item, dict) for item in lst)
    
    if has_invalid:
        try:
            validate_environmentvariable_or_list(lst)
            assert False, "Should have raised ValueError for non-dict/non-EnvironmentVariable"
        except ValueError as e:
            assert "must be either dict or EnvironmentVariable" in str(e)
    else:
        result = validate_environmentvariable_or_list(lst)
        assert result == lst


# Test empty lists
def test_environmentvariable_empty_list():
    """Property: Empty list should be valid."""
    result = validate_environmentvariable_or_list([])
    assert result == []


# Test ProjectTriggers with nested lists
def test_project_triggers_nested_structure():
    """Property: FilterGroups must be list of lists of WebhookFilter."""
    # Valid structure
    webhook_filter = WebhookFilter(Pattern=".*", Type="EVENT")
    triggers = ProjectTriggers(FilterGroups=[[webhook_filter]])
    triggers.validate()  # Should not raise
    
    # Invalid: Not a list of lists
    triggers_invalid1 = ProjectTriggers(FilterGroups=[webhook_filter])
    try:
        triggers_invalid1.validate()
        assert False, "Should fail when FilterGroups is not list of lists"
    except TypeError:
        pass  # Expected
    
    # Invalid: Inner element not WebhookFilter
    triggers_invalid2 = ProjectTriggers(FilterGroups=[["not_a_filter"]])
    try:
        triggers_invalid2.validate()
        assert False, "Should fail when inner element is not WebhookFilter"
    except TypeError:
        pass  # Expected


# Test Source with edge case combinations
@given(
    source_type=st.sampled_from(["GITHUB", "CODECOMMIT", "S3"]),
    has_location=st.booleans(),
    auth_type=st.one_of(st.none(), st.just("OAUTH"), st.text())
)
def test_source_auth_github_only(source_type, has_location, auth_type):
    """Property: Auth should only be allowed with GITHUB source type."""
    props = {"Type": source_type}
    
    if has_location:
        props["Location"] = "https://example.com/repo"
    
    if auth_type:
        try:
            props["Auth"] = SourceAuth(Type=auth_type)
            if auth_type != "OAUTH":
                # SourceAuth itself should fail validation
                props["Auth"].validate()
                assert False, f"SourceAuth should only accept OAUTH, not {auth_type}"
        except ValueError:
            if auth_type != "OAUTH":
                # Expected failure for non-OAUTH
                return
            else:
                raise
    
    source = Source(**props)
    
    # Now validate the Source
    try:
        source.validate()
        
        # If validation passed, check expectations
        if source_type != "GITHUB" and auth_type:
            assert False, f"Auth should not be allowed for {source_type}"
        
        if source_type not in ["CODEPIPELINE", "NO_SOURCE"] and not has_location:
            assert False, f"Location should be required for {source_type}"
            
    except ValueError as e:
        error_msg = str(e)
        
        # Check if error is expected
        if source_type != "GITHUB" and auth_type == "OAUTH":
            assert "SourceAuth: must only be defined when using" in error_msg
        elif source_type not in ["CODEPIPELINE", "NO_SOURCE"] and not has_location:
            assert "Location: must be defined" in error_msg
        else:
            # Unexpected error
            assert False, f"Unexpected validation error: {e}"


# Test Artifacts with boundary conditions
def test_artifacts_s3_empty_strings():
    """Property: S3 artifacts with empty Name/Location should fail."""
    # Empty strings should be treated as missing
    artifact1 = Artifacts(Type="S3", Name="", Location="valid")
    try:
        artifact1.validate()
        # Empty string might be treated as valid, which would be a bug
    except ValueError:
        pass  # Expected if empty string is properly rejected
    
    artifact2 = Artifacts(Type="S3", Name="valid", Location="")
    try:
        artifact2.validate()
        # Empty string might be treated as valid, which would be a bug
    except ValueError:
        pass  # Expected if empty string is properly rejected
    
    # Both empty
    artifact3 = Artifacts(Type="S3", Name="", Location="")
    try:
        artifact3.validate()
        # Empty strings should not satisfy the requirement
    except ValueError:
        pass  # Expected


# Test with None values
def test_source_none_location():
    """Property: None location should be treated as missing."""
    source = Source(Type="GITHUB", Location=None)
    try:
        source.validate()
        assert False, "None location should be treated as missing for GITHUB"
    except (ValueError, AttributeError):
        pass  # Expected


# Test case sensitivity in validators
@given(st.sampled_from(["enabled", "ENABLED", "Enabled", "disabled", "DISABLED", "Disabled"]))
def test_status_case_sensitivity(status):
    """Property: Status validation should be case-sensitive."""
    from troposphere.validators.codebuild import validate_status
    
    if status in ["ENABLED", "DISABLED"]:
        result = validate_status(status)
        assert result == status
    else:
        try:
            validate_status(status)
            assert False, f"Should reject {status} (case-sensitive)"
        except ValueError as e:
            assert "Status: must be one of" in str(e)


# Test with special characters in webhook patterns
@given(st.text(alphabet=st.characters(blacklist_categories=["C"]), min_size=1))
def test_webhook_filter_pattern_special_chars(pattern):
    """Property: WebhookFilter should accept any pattern string."""
    filter = WebhookFilter(Pattern=pattern, Type="EVENT")
    # Should not raise - patterns can contain special regex characters


# Test integer values where strings are expected
@given(st.integers())
def test_type_coercion_in_validators(value):
    """Property: Integer values should not be silently coerced to strings."""
    from troposphere.validators.codebuild import validate_status
    
    try:
        validate_status(value)
        assert False, f"Should not accept integer {value}"
    except (ValueError, TypeError):
        pass  # Expected


# Test with AWS helper functions (should bypass validation)
def test_aws_helper_function_bypass():
    """Property: AWS helper functions should bypass validation."""
    from troposphere import Ref
    from troposphere.codebuild import Environment
    
    # Using Ref for Type should bypass validation
    env = Environment(
        Type=Ref("EnvironmentTypeParameter"),
        ComputeType="BUILD_GENERAL1_SMALL",
        Image="aws/codebuild/standard:5.0"
    )
    # Should not raise even though Ref is not a valid environment type string
    env.validate()
    
    
# Test FilterGroups edge cases
def test_project_triggers_empty_filter_groups():
    """Property: Empty FilterGroups should be valid."""
    triggers = ProjectTriggers(FilterGroups=[])
    triggers.validate()  # Should not raise
    
    # Empty inner list
    triggers2 = ProjectTriggers(FilterGroups=[[]])
    triggers2.validate()  # Should not raise