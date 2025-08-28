import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings, example
import troposphere.cloud9 as cloud9
from troposphere import AWSHelperFn, Ref, GetAtt

# Test with extreme Unicode and special characters
unicode_strategy = st.text(
    alphabet=st.characters(min_codepoint=0x00, max_codepoint=0x10FFFF),
    min_size=1,
    max_size=200
)

# Test with very long strings
long_text_strategy = st.text(min_size=1000, max_size=10000)

# Test with whitespace-only strings
whitespace_strategy = st.text(alphabet=" \t\n\r", min_size=1, max_size=100)

@given(
    path=unicode_strategy,
    url=unicode_strategy
)
@settings(max_examples=200)
def test_repository_unicode_handling(path, url):
    """Test Repository with Unicode characters"""
    try:
        repo = cloud9.Repository(
            PathComponent=path,
            RepositoryUrl=url
        )
        dict_repr = repo.to_dict()
        
        # Try round-trip
        reconstructed = cloud9.Repository._from_dict(**dict_repr)
        assert repo == reconstructed
    except (UnicodeDecodeError, UnicodeEncodeError) as e:
        # This would be a bug - Unicode should be handled
        raise AssertionError(f"Unicode handling bug: {e}")


@given(
    path=st.one_of(
        st.just(""),
        whitespace_strategy,
        st.just(None)
    )
)
def test_repository_empty_values(path):
    """Test Repository with empty/whitespace values"""
    if path is None:
        # Should fail for None values on required fields
        try:
            repo = cloud9.Repository(
                PathComponent=path,
                RepositoryUrl="http://example.com"
            )
            assert False, "Should reject None for required field"
        except (TypeError, AttributeError):
            pass  # Expected
    else:
        # Empty strings might be accepted
        repo = cloud9.Repository(
            PathComponent=path,
            RepositoryUrl="http://example.com"
        )
        dict_repr = repo.to_dict()
        assert dict_repr["PathComponent"] == path


@given(
    stop_time=st.one_of(
        st.just(float('inf')),
        st.just(float('-inf')),
        st.just(float('nan')),
        st.floats(allow_nan=True, allow_infinity=True),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_automatic_stop_invalid_types(stop_time):
    """Test AutomaticStopTimeMinutes with invalid types"""
    try:
        env = cloud9.EnvironmentEC2(
            "TestEnv",
            ImageId="ami-12345678",
            InstanceType="t2.micro",
            AutomaticStopTimeMinutes=stop_time
        )
        dict_repr = env.to_dict()
        
        # If we get here, the value was accepted
        # Check if it's actually a valid integer
        if not isinstance(stop_time, (int, str, bytes)) or (isinstance(stop_time, str) and not stop_time.isdigit()):
            if isinstance(stop_time, float) and (stop_time != stop_time or stop_time in [float('inf'), float('-inf')]):
                # NaN or infinity should not be accepted as valid integers
                assert False, f"Invalid value {stop_time} was accepted for integer field"
    except (ValueError, TypeError):
        # Expected for invalid types
        pass


@given(
    image_id=st.text(),
    instance_type=st.text()
)
@settings(max_examples=200) 
def test_environment_no_validation_mode(image_id, instance_type):
    """Test that no_validation() bypasses validation"""
    env = cloud9.EnvironmentEC2(
        "TestEnv",
        ImageId=image_id,
        InstanceType=instance_type
    )
    
    # Without validation, any values should work
    env_no_val = env.no_validation()
    dict_repr = env_no_val.to_dict(validation=False)
    
    assert "Properties" in dict_repr
    assert dict_repr["Properties"]["ImageId"] == image_id
    assert dict_repr["Properties"]["InstanceType"] == instance_type


@given(st.data())
def test_helper_function_values(data):
    """Test using AWS helper functions as values"""
    # These should be accepted without validation
    ref = Ref("SomeResource")
    
    env = cloud9.EnvironmentEC2(
        "TestEnv",
        ImageId=ref,  # Using Ref as ImageId
        InstanceType="t2.micro"
    )
    
    dict_repr = env.to_dict()
    assert "Properties" in dict_repr
    # The Ref should be preserved in the output
    assert dict_repr["Properties"]["ImageId"] == ref.to_dict()


@given(
    repos=st.lists(
        st.one_of(
            st.builds(
                cloud9.Repository,
                PathComponent=st.text(min_size=1),
                RepositoryUrl=st.text(min_size=1)
            ),
            st.none(),
            st.text(),
            st.integers(),
            st.dictionaries(st.text(), st.text())
        ),
        min_size=1,
        max_size=10
    )
)
def test_repositories_mixed_types(repos):
    """Test Repositories field with mixed/invalid types"""
    try:
        # Filter out valid Repository objects
        valid_repos = [r for r in repos if isinstance(r, cloud9.Repository)]
        invalid_repos = [r for r in repos if not isinstance(r, cloud9.Repository)]
        
        if invalid_repos:
            # Should fail with invalid types in the list
            env = cloud9.EnvironmentEC2(
                "TestEnv",
                ImageId="ami-12345678",
                InstanceType="t2.micro",
                Repositories=repos
            )
            env.to_dict()  # Trigger validation
            
            # If we get here with invalid repos, that's a bug
            assert False, f"Invalid repository types {invalid_repos} were accepted"
    except (TypeError, ValueError, AttributeError):
        # Expected for invalid types
        pass


@given(
    title=st.one_of(
        st.text(alphabet=st.characters(blacklist_categories=('Lu', 'Ll', 'Nd')), min_size=1),
        st.text(min_size=0, max_size=0),
        st.from_regex(r"[^a-zA-Z0-9]+", fullmatch=True)
    )
)
def test_environment_title_validation(title):
    """Test title validation for EnvironmentEC2"""
    try:
        env = cloud9.EnvironmentEC2(
            title,
            ImageId="ami-12345678", 
            InstanceType="t2.micro"
        )
        env.validate_title()
        
        # If validation passes, title should be alphanumeric
        assert all(c.isalnum() for c in title), f"Non-alphanumeric title '{title}' passed validation"
    except ValueError as e:
        # Should fail for non-alphanumeric titles
        assert "not alphanumeric" in str(e)


@given(
    data=st.dictionaries(
        st.text(),
        st.one_of(st.text(), st.integers(), st.lists(st.text()))
    )
)
def test_from_dict_with_extra_fields(data):
    """Test from_dict with unexpected fields"""
    # Add required fields
    data["ImageId"] = "ami-12345678"
    data["InstanceType"] = "t2.micro"
    
    # Add some random extra fields
    extra_fields = {f"ExtraField{i}": f"value{i}" for i in range(3)}
    data.update(extra_fields)
    
    try:
        env = cloud9.EnvironmentEC2.from_dict("TestEnv", data)
        # Extra fields should be rejected
        for field in extra_fields:
            assert not hasattr(env, field), f"Extra field {field} was incorrectly accepted"
    except AttributeError as e:
        # Expected - extra fields should cause an error
        assert any(field in str(e) for field in extra_fields)