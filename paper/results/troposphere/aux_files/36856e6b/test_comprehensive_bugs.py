"""Comprehensive bug hunting tests for troposphere.codebuild."""

from hypothesis import given, strategies as st, assume, settings
import traceback
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.codebuild import (
    Source, SourceAuth, Artifacts, ProjectTriggers, 
    WebhookFilter, ProjectCache, Environment, EnvironmentVariable
)


# Test for potential dictionary key errors
@given(
    artifact_type=st.sampled_from(["S3", "CODEPIPELINE", "NO_ARTIFACTS"]),
    include_type=st.booleans()
)
def test_artifacts_missing_type_key(artifact_type, include_type):
    """Property: Validation should handle missing Type gracefully."""
    artifact = Artifacts()
    if include_type:
        artifact.properties["Type"] = artifact_type
    
    try:
        artifact.validate()
        if not include_type:
            # Missing Type should fail
            assert False, "Should fail when Type is missing"
    except (ValueError, KeyError) as e:
        if not include_type:
            # Expected to fail
            pass
        else:
            # Should not fail if Type is included
            if artifact_type != "S3":
                assert False, f"Unexpected error for type {artifact_type}: {e}"


# Test attribute access vs properties dictionary
def test_properties_vs_attributes():
    """Test: Does validation use properties dict or object attributes?"""
    
    # Create Source with Type in properties
    source = Source(Type="GITHUB", Location="https://github.com/repo")
    
    # Directly modify properties dict
    source.properties["Type"] = "INVALID_TYPE"
    
    try:
        source.validate()
        assert False, "Should fail with invalid type"
    except ValueError as e:
        assert "Source Type: must be one of" in str(e)
    
    # Now test if validation reads from properties correctly
    source2 = Source(Type="GITHUB", Location="https://github.com/repo")
    
    # Remove Type from properties dict
    del source2.properties["Type"]
    
    try:
        source2.validate()
        assert False, "Should fail when Type is missing from properties"
    except (ValueError, KeyError) as e:
        # Should get KeyError or handle gracefully
        print(f"Error when Type missing: {e}")


# Test WebhookFilter with extreme patterns
@given(pattern=st.text(min_size=0, max_size=10000))
def test_webhook_filter_extreme_patterns(pattern):
    """Property: WebhookFilter should handle any pattern length."""
    filter = WebhookFilter(Pattern=pattern, Type="EVENT")
    # Should not crash regardless of pattern


# Test validation method inheritance
def test_validation_inheritance():
    """Test: Do subclasses properly inherit and call parent validation?"""
    
    # SourceAuth inherits from AWSProperty
    auth = SourceAuth(Type="INVALID")
    try:
        auth.validate()
        assert False, "Should reject invalid auth type"
    except ValueError as e:
        assert "SourceAuth Type: must be one of" in str(e)


# Test with properties that reference other properties
def test_interdependent_validation():
    """Test: Source validation depends on multiple properties."""
    
    # GITHUB with Auth but Auth has invalid type
    try:
        auth = SourceAuth(Type="INVALID")
        source = Source(Type="GITHUB", Location="https://github.com/repo", Auth=auth)
        # Auth validation happens in SourceAuth.validate(), not Source.validate()
        auth.validate()  # This should fail
        assert False, "Should fail with invalid auth type"
    except ValueError as e:
        assert "SourceAuth Type" in str(e)


# Test FilterGroups with deeply nested invalid structure
@given(
    depth=st.integers(min_value=0, max_value=5),
    width=st.integers(min_value=0, max_value=5)
)
def test_project_triggers_nested_validation(depth, width):
    """Property: FilterGroups validation should handle nested structures."""
    
    # Create nested structure
    if depth == 0:
        filter_groups = []
    elif depth == 1:
        filter_groups = [[WebhookFilter(Pattern="test", Type="EVENT") for _ in range(width)]]
    else:
        # Create invalid nested structure
        filter_groups = [["invalid"] * width]
    
    triggers = ProjectTriggers(FilterGroups=filter_groups)
    
    if depth <= 1:
        # Should pass
        triggers.validate()
    else:
        # Should fail with invalid structure
        try:
            triggers.validate()
            assert False, "Should fail with invalid nested structure"
        except (TypeError, AttributeError):
            pass  # Expected


# Test Environment with conflicting properties
def test_environment_conflicting_properties():
    """Test: Environment with both Fleet and direct compute settings."""
    from troposphere.codebuild import ProjectFleet
    
    env = Environment(
        Type="LINUX_CONTAINER",
        ComputeType="BUILD_GENERAL1_SMALL",
        Image="aws/codebuild/standard:5.0",
        Fleet=ProjectFleet(FleetArn="arn:aws:codebuild:us-east-1:123456789:fleet/test")
    )
    
    # Should this be allowed? Let's see
    env.validate()  # If this passes, there might be a validation gap


# Test with Unicode and special characters
@given(
    name=st.text(alphabet=st.characters(min_codepoint=0x1F600, max_codepoint=0x1F64F), min_size=1),  # Emojis
    value=st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cf"]), min_size=1)
)
def test_environment_variable_unicode(name, value):
    """Property: EnvironmentVariable should handle Unicode correctly."""
    try:
        env_var = EnvironmentVariable(Name=name, Value=value, Type="PLAINTEXT")
        env_var.validate()
        # Unicode should work
    except Exception as e:
        # Check if it's a Unicode handling issue
        if "codec" in str(e) or "decode" in str(e) or "encode" in str(e):
            print(f"Unicode handling issue: {e}")
            assert False, f"Unicode handling failed: {e}"


# Test caching behavior in validation
def test_validation_caching():
    """Test: Does validation cache results inappropriately?"""
    
    artifact = Artifacts(Type="S3", Name="test", Location="s3://bucket")
    
    # First validation should pass
    artifact.validate()
    
    # Modify properties
    artifact.properties["Type"] = "INVALID"
    
    # Second validation should fail
    try:
        artifact.validate()
        assert False, "Should fail after modifying Type"
    except ValueError as e:
        assert "Artifacts Type: must be one of" in str(e)


# Test required vs optional property enforcement
@given(
    has_name=st.booleans(),
    has_value=st.booleans(),
    has_type=st.booleans()
)
def test_environment_variable_required_properties(has_name, has_value, has_type):
    """Property: EnvironmentVariable enforces required Name and Value."""
    props = {}
    if has_name:
        props["Name"] = "TEST"
    if has_value:
        props["Value"] = "value"
    if has_type:
        props["Type"] = "PLAINTEXT"
    
    try:
        env_var = EnvironmentVariable(**props)
        # Object creation might fail if required props missing
        env_var.validate()
        
        # Should only succeed if both Name and Value present
        assert has_name and has_value, "Should require Name and Value"
        
    except (TypeError, ValueError) as e:
        # Should fail if Name or Value missing
        assert not (has_name and has_value), f"Should not fail with Name and Value present: {e}"


if __name__ == "__main__":
    # Run property tests with explicit examples
    print("Running comprehensive bug hunting tests...")
    
    # Run a quick check of each test
    test_properties_vs_attributes()
    print("✓ Properties vs attributes test passed")
    
    test_validation_inheritance()
    print("✓ Validation inheritance test passed")
    
    test_interdependent_validation()
    print("✓ Interdependent validation test passed")
    
    test_environment_conflicting_properties()
    print("✓ Environment conflicting properties test passed")
    
    test_validation_caching()
    print("✓ Validation caching test passed")
    
    print("\nAll manual tests passed!")