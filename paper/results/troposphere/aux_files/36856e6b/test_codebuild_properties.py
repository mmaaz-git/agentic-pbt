"""Property-based tests for troposphere.codebuild validation functions."""

import sys
import traceback
from hypothesis import given, strategies as st, assume, settings
from troposphere.codebuild import (
    Artifacts, EnvironmentVariable, Environment, ProjectCache,
    Source, SourceAuth, ProjectTriggers, WebhookFilter
)
from troposphere.validators.codebuild import (
    validate_environmentvariable_or_list,
    validate_image_pull_credentials,
    validate_credentials_provider,
    validate_webhookfilter_type,
    validate_projectfilesystemlocation_type,
    validate_source_auth,
    validate_artifacts,
    validate_environment_variable,
    validate_environment,
    validate_project_cache,
    validate_source,
    validate_project_triggers,
    validate_status
)


# Test 1: validate_image_pull_credentials - should only accept specific values
@given(st.text())
def test_image_pull_credentials_invalid_input(s):
    """Property: Invalid credentials should raise ValueError."""
    assume(s not in ["CODEBUILD", "SERVICE_ROLE"])
    try:
        validate_image_pull_credentials(s)
        assert False, f"Should have raised ValueError for {s}"
    except ValueError as e:
        assert "ImagePullCredentialsType must be one of" in str(e)


@given(st.sampled_from(["CODEBUILD", "SERVICE_ROLE"]))
def test_image_pull_credentials_valid_input(s):
    """Property: Valid credentials should pass through unchanged."""
    result = validate_image_pull_credentials(s)
    assert result == s


# Test 2: validate_credentials_provider - only accepts "SECRETS_MANAGER"
@given(st.text())
def test_credentials_provider_invalid(s):
    """Property: Invalid provider should raise ValueError."""
    assume(s != "SECRETS_MANAGER")
    try:
        validate_credentials_provider(s)
        assert False, f"Should have raised ValueError for {s}"
    except ValueError as e:
        assert "CredentialProvider must be one of" in str(e)


@given(st.just("SECRETS_MANAGER"))
def test_credentials_provider_valid(s):
    """Property: Valid provider passes through unchanged."""
    result = validate_credentials_provider(s)
    assert result == s


# Test 3: validate_webhookfilter_type - must be one of specific types
VALID_WEBHOOK_TYPES = ["EVENT", "ACTOR_ACCOUNT_ID", "HEAD_REF", "BASE_REF", "FILE_PATH"]

@given(st.text())
def test_webhookfilter_type_invalid(s):
    """Property: Invalid webhook filter type should raise ValueError."""
    assume(s not in VALID_WEBHOOK_TYPES)
    try:
        validate_webhookfilter_type(s)
        assert False, f"Should have raised ValueError for {s}"
    except ValueError as e:
        assert "Webhookfilter Type must be one of" in str(e)


@given(st.sampled_from(VALID_WEBHOOK_TYPES))
def test_webhookfilter_type_valid(s):
    """Property: Valid webhook filter type passes through unchanged."""
    result = validate_webhookfilter_type(s)
    assert result == s


# Test 4: validate_projectfilesystemlocation_type - only accepts "EFS"
@given(st.text())
def test_projectfilesystemlocation_type_invalid(s):
    """Property: Invalid filesystem type should raise ValueError."""
    assume(s != "EFS")
    try:
        validate_projectfilesystemlocation_type(s)
        assert False, f"Should have raised ValueError for {s}"
    except ValueError as e:
        assert "ProjectFileSystemLocation Type must be one of" in str(e)


# Test 5: validate_status - only accepts ENABLED or DISABLED
@given(st.text())
def test_status_invalid(s):
    """Property: Invalid status should raise ValueError."""
    assume(s not in ["ENABLED", "DISABLED"])
    try:
        validate_status(s)
        assert False, f"Should have raised ValueError for {s}"
    except ValueError as e:
        assert "Status: must be one of" in str(e)


@given(st.sampled_from(["ENABLED", "DISABLED"]))
def test_status_valid(s):
    """Property: Valid status passes through unchanged."""
    result = validate_status(s)
    assert result == s


# Test 6: Artifacts validation with S3 type requiring Name and Location
@given(
    artifact_type=st.sampled_from(["CODEPIPELINE", "NO_ARTIFACTS", "S3"]),
    name=st.one_of(st.none(), st.text(min_size=1)),
    location=st.one_of(st.none(), st.text(min_size=1))
)
def test_artifacts_validation(artifact_type, name, location):
    """Property: S3 artifacts require Name and Location, others don't."""
    props = {"Type": artifact_type}
    if name:
        props["Name"] = name
    if location:
        props["Location"] = location
    
    artifact = Artifacts(**props)
    
    if artifact_type == "S3":
        # S3 requires both Name and Location
        if not name or not location:
            try:
                artifact.validate()
                assert False, "S3 should require Name and Location"
            except ValueError as e:
                assert "requires" in str(e) and ("Name" in str(e) or "Location" in str(e))
        else:
            # Should not raise
            artifact.validate()
    else:
        # Non-S3 types should always validate
        artifact.validate()


# Test 7: EnvironmentVariable Type validation
@given(
    var_type=st.one_of(
        st.none(),
        st.sampled_from(["PARAMETER_STORE", "PLAINTEXT", "SECRETS_MANAGER"]),
        st.text()
    )
)
def test_environment_variable_type(var_type):
    """Property: EnvironmentVariable Type must be one of valid types or absent."""
    props = {"Name": "TEST_VAR", "Value": "test_value"}
    if var_type is not None:
        props["Type"] = var_type
    
    env_var = EnvironmentVariable(**props)
    
    if var_type is None or var_type in ["PARAMETER_STORE", "PLAINTEXT", "SECRETS_MANAGER"]:
        # Should validate successfully
        env_var.validate()
    else:
        # Should raise for invalid type
        try:
            env_var.validate()
            assert False, f"Should have raised ValueError for Type={var_type}"
        except ValueError as e:
            assert "EnvironmentVariable Type: must be one of" in str(e)


# Test 8: Environment Type validation
VALID_ENV_TYPES = [
    "ARM_CONTAINER", "LINUX_CONTAINER", "LINUX_GPU_CONTAINER",
    "WINDOWS_CONTAINER", "WINDOWS_SERVER_2019_CONTAINER"
]

@given(env_type=st.text())
def test_environment_type_invalid(env_type):
    """Property: Invalid environment type should raise ValueError."""
    assume(env_type not in VALID_ENV_TYPES)
    
    env = Environment(
        Type=env_type,
        ComputeType="BUILD_GENERAL1_SMALL",
        Image="aws/codebuild/standard:5.0"
    )
    
    try:
        env.validate()
        assert False, f"Should have raised ValueError for Type={env_type}"
    except ValueError as e:
        assert "Environment Type: must be one of" in str(e)


# Test 9: ProjectCache Type validation
@given(cache_type=st.text())
def test_project_cache_type_invalid(cache_type):
    """Property: Invalid cache type should raise ValueError."""
    assume(cache_type not in ["NO_CACHE", "LOCAL", "S3"])
    
    cache = ProjectCache(Type=cache_type)
    
    try:
        cache.validate()
        assert False, f"Should have raised ValueError for Type={cache_type}"
    except ValueError as e:
        assert "ProjectCache Type: must be one of" in str(e)


# Test 10: Source validation - complex rules
@given(
    source_type=st.sampled_from([
        "BITBUCKET", "CODECOMMIT", "CODEPIPELINE", "GITHUB",
        "GITHUB_ENTERPRISE", "GITLAB", "GITLAB_SELF_MANAGED", "NO_SOURCE", "S3"
    ]),
    location=st.one_of(st.none(), st.text(min_size=1)),
    has_auth=st.booleans()
)
def test_source_validation(source_type, location, has_auth):
    """Property: Source validation enforces location and auth requirements."""
    props = {"Type": source_type}
    if location:
        props["Location"] = location
    if has_auth:
        props["Auth"] = SourceAuth(Type="OAUTH")
    
    source = Source(**props)
    
    location_agnostic = ["CODEPIPELINE", "NO_SOURCE"]
    
    try:
        source.validate()
        # Validation passed, check if it should have
        if source_type not in location_agnostic and not location:
            assert False, f"Should require Location for {source_type}"
        if has_auth and source_type != "GITHUB":
            assert False, f"Auth should only be allowed for GITHUB, not {source_type}"
    except ValueError as e:
        # Validation failed, check if it should have
        error_msg = str(e)
        if source_type not in location_agnostic and not location:
            assert "Location: must be defined" in error_msg
        elif has_auth and source_type != "GITHUB":
            assert "SourceAuth: must only be defined when using" in error_msg
        else:
            # Unexpected error
            assert False, f"Unexpected error: {e}"


# Test 11: SourceAuth Type must be OAUTH
@given(auth_type=st.text())
def test_source_auth_type(auth_type):
    """Property: SourceAuth Type must be 'OAUTH'."""
    auth = SourceAuth(Type=auth_type)
    
    if auth_type == "OAUTH":
        auth.validate()
    else:
        try:
            auth.validate()
            assert False, f"Should have raised ValueError for Type={auth_type}"
        except ValueError as e:
            assert "SourceAuth Type: must be one of" in str(e)


# Test 12: validate_environmentvariable_or_list type checking
@given(
    data=st.one_of(
        st.none(),
        st.text(),
        st.integers(),
        st.lists(st.one_of(
            st.dictionaries(st.text(), st.text()),
            st.text(),
            st.integers()
        ))
    )
)
def test_environmentvariable_or_list_type_checking(data):
    """Property: Function should only accept lists of dicts or EnvironmentVariable objects."""
    if not isinstance(data, list):
        try:
            validate_environmentvariable_or_list(data)
            assert False, f"Should have raised ValueError for non-list {type(data)}"
        except ValueError as e:
            assert "must be a list" in str(e)
    else:
        # It's a list, check elements
        valid = all(isinstance(elem, dict) for elem in data)
        if valid:
            result = validate_environmentvariable_or_list(data)
            assert result == data
        else:
            try:
                validate_environmentvariable_or_list(data)
                assert False, f"Should have raised ValueError for invalid list elements"
            except ValueError as e:
                assert "must be either dict or EnvironmentVariable" in str(e)