#!/usr/bin/env python3
"""Property-based tests for troposphere.codestar module."""

import json
import sys
import traceback
from hypothesis import given, strategies as st, assume, settings

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codestar as codestar
from troposphere import validators


# Test 1: Round-trip serialization property
@given(
    bucket=st.text(min_size=1, max_size=63).filter(lambda x: x.strip()),
    key=st.text(min_size=1, max_size=1024).filter(lambda x: x.strip()),
    object_version=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_s3_round_trip_serialization(bucket, key, object_version):
    """Test that S3 objects can be serialized to dict and deserialized back."""
    # Create original object
    original = codestar.S3(
        Bucket=bucket,
        Key=key
    )
    if object_version is not None:
        original.ObjectVersion = object_version
    
    # Serialize to dict
    serialized = original.to_dict()
    
    # Deserialize back
    reconstructed = codestar.S3._from_dict(**serialized)
    
    # They should be equal
    assert original.to_dict() == reconstructed.to_dict()


# Test 2: GitHubRepository round-trip with complex properties
@given(
    repo_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip() and x.replace('-', '').replace('_', '').replace('.', '').isalnum()),
    repo_owner=st.text(min_size=1, max_size=39).filter(lambda x: x.strip() and x.replace('-', '').isalnum()),
    enable_issues=st.booleans(),
    is_private=st.booleans(),
    description=st.one_of(st.none(), st.text(max_size=350))
)
def test_github_repository_round_trip(repo_name, repo_owner, enable_issues, is_private, description):
    """Test GitHubRepository serialization round-trip."""
    repo = codestar.GitHubRepository(
        title="TestRepo",
        RepositoryName=repo_name,
        RepositoryOwner=repo_owner,
        EnableIssues=enable_issues,
        IsPrivate=is_private
    )
    if description is not None:
        repo.RepositoryDescription = description
    
    # Serialize and deserialize
    serialized = repo.to_dict()
    reconstructed = codestar.GitHubRepository.from_dict("TestRepo", serialized["Properties"])
    
    # Should be equal
    assert repo.to_dict() == reconstructed.to_dict()


# Test 3: Boolean validator property
@given(
    value=st.one_of(
        st.sampled_from([True, 1, "1", "true", "True"]),
        st.sampled_from([False, 0, "0", "false", "False"])
    )
)
def test_boolean_validator_consistency(value):
    """Test that boolean validator consistently converts various true/false representations."""
    result = validators.boolean(value)
    
    # Should always return a bool
    assert isinstance(result, bool)
    
    # Check consistency
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


# Test 4: Boolean validator idempotence
@given(
    value=st.one_of(
        st.sampled_from([True, 1, "1", "true", "True"]),
        st.sampled_from([False, 0, "0", "false", "False"])
    )
)
def test_boolean_validator_idempotence(value):
    """Test that applying boolean validator twice gives same result as once."""
    once = validators.boolean(value)
    twice = validators.boolean(once)
    
    assert once == twice


# Test 5: Required property validation
@given(
    bucket=st.text(min_size=1, max_size=63).filter(lambda x: x.strip()),
    key=st.text(min_size=1, max_size=1024).filter(lambda x: x.strip())
)
def test_s3_required_properties(bucket, key):
    """Test that S3 object validates required properties."""
    # Should work with all required properties
    s3 = codestar.S3(Bucket=bucket, Key=key)
    s3.to_dict()  # This triggers validation
    
    # Should fail without required properties
    try:
        s3_missing = codestar.S3(Bucket=bucket)  # Missing Key
        s3_missing.to_dict()
        assert False, "Should have raised ValueError for missing required property"
    except ValueError as e:
        assert "required" in str(e).lower()


# Test 6: Code object with nested S3
@given(
    bucket=st.text(min_size=1, max_size=63).filter(lambda x: x.strip()),
    key=st.text(min_size=1, max_size=1024).filter(lambda x: x.strip())
)
def test_code_with_nested_s3(bucket, key):
    """Test Code object with nested S3 property."""
    s3 = codestar.S3(Bucket=bucket, Key=key)
    code = codestar.Code(S3=s3)
    
    # Serialize
    serialized = code.to_dict()
    
    # Should have nested structure
    assert "S3" in serialized
    assert "Bucket" in serialized["S3"]
    assert "Key" in serialized["S3"]
    assert serialized["S3"]["Bucket"] == bucket
    assert serialized["S3"]["Key"] == key
    
    # Round-trip
    reconstructed = codestar.Code._from_dict(**serialized)
    assert code.to_dict() == reconstructed.to_dict()


# Test 7: GitHubRepository required properties
@given(
    repo_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    repo_owner=st.text(min_size=1, max_size=39).filter(lambda x: x.strip())
)
def test_github_repository_required_props(repo_name, repo_owner):
    """Test that GitHubRepository validates required properties."""
    # Should work with required properties
    repo = codestar.GitHubRepository(
        title="TestRepo",
        RepositoryName=repo_name,
        RepositoryOwner=repo_owner
    )
    repo.to_dict()  # Triggers validation
    
    # Should fail without required properties
    try:
        repo_missing = codestar.GitHubRepository(
            title="TestRepo",
            RepositoryName=repo_name
            # Missing RepositoryOwner
        )
        repo_missing.to_dict()
        assert False, "Should have raised ValueError for missing required property"
    except ValueError as e:
        assert "required" in str(e).lower()


# Test 8: Equality property
@given(
    repo_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    repo_owner=st.text(min_size=1, max_size=39).filter(lambda x: x.strip()),
    enable_issues=st.booleans()
)
def test_github_repository_equality(repo_name, repo_owner, enable_issues):
    """Test that repositories with same properties are equal."""
    repo1 = codestar.GitHubRepository(
        title="TestRepo",
        RepositoryName=repo_name,
        RepositoryOwner=repo_owner,
        EnableIssues=enable_issues
    )
    
    repo2 = codestar.GitHubRepository(
        title="TestRepo",
        RepositoryName=repo_name,
        RepositoryOwner=repo_owner,
        EnableIssues=enable_issues
    )
    
    # Should be equal
    assert repo1 == repo2
    
    # Should have same hash
    assert hash(repo1) == hash(repo2)


# Test 9: Type validation for boolean properties
@given(
    invalid_value=st.one_of(
        st.text(min_size=1).filter(lambda x: x not in ["true", "True", "false", "False", "0", "1"]),
        st.integers(min_value=2),
        st.floats(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_boolean_validator_rejects_invalid(invalid_value):
    """Test that boolean validator rejects invalid values."""
    try:
        validators.boolean(invalid_value)
        assert False, f"Should have rejected {invalid_value!r}"
    except ValueError:
        pass  # Expected


# Test 10: JSON serialization property
@given(
    repo_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip() and not any(c in x for c in ['"', '\\', '\n', '\r', '\t'])),
    repo_owner=st.text(min_size=1, max_size=39).filter(lambda x: x.strip() and not any(c in x for c in ['"', '\\', '\n', '\r', '\t'])),
    description=st.one_of(
        st.none(),
        st.text(max_size=350).filter(lambda x: not any(c in x for c in ['"', '\\', '\n', '\r', '\t']))
    )
)
def test_json_serialization(repo_name, repo_owner, description):
    """Test that objects can be serialized to valid JSON."""
    repo = codestar.GitHubRepository(
        title="TestRepo",
        RepositoryName=repo_name,
        RepositoryOwner=repo_owner
    )
    if description is not None:
        repo.RepositoryDescription = description
    
    # Serialize to JSON
    json_str = repo.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Should contain expected structure
    assert "Type" in parsed
    assert parsed["Type"] == "AWS::CodeStar::GitHubRepository"
    assert "Properties" in parsed
    assert "RepositoryName" in parsed["Properties"]
    assert parsed["Properties"]["RepositoryName"] == repo_name


if __name__ == "__main__":
    # Run all tests
    print("Running property-based tests for troposphere.codestar...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])