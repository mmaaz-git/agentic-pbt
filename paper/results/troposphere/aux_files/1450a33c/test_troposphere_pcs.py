"""Property-based tests for troposphere.pcs module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import math
import string
import json
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import troposphere.pcs as pcs
from troposphere.validators import integer


# Property 1: Integer validator accepts valid inputs and rejects invalid
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x)),
    st.text(string.digits).filter(lambda s: s and not s.startswith('0') or s == '0')
))
def test_integer_validator_accepts_valid(value):
    """Test that integer validator accepts values that can be converted to int"""
    result = integer(value)
    # Should return the same value
    assert result == value
    # Should be convertible to int
    int(result)


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)),
    st.text(string.ascii_letters + string.punctuation),
    st.just(float('inf')),
    st.just(float('-inf')),
    st.just(float('nan')),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_rejects_invalid(value):
    """Test that integer validator rejects values that cannot be converted to int"""
    # Skip values that might actually be valid integers
    try:
        int(value)
        assume(False)  # Skip if it's actually convertible
    except (ValueError, TypeError):
        pass
    
    # Should raise ValueError for invalid inputs
    try:
        integer(value)
        assert False, f"Expected ValueError for {value}"
    except ValueError as e:
        assert "is not a valid integer" in str(e)


# Property 2: Required property validation
@given(st.text(string.ascii_letters + string.digits).filter(lambda s: s))
def test_required_properties_validation(cluster_name):
    """Test that required properties are enforced"""
    # Cluster requires Networking, Scheduler, and Size
    try:
        cluster = pcs.Cluster(cluster_name)
        cluster.to_dict()  # This triggers validation
        assert False, "Should have raised ValueError for missing required properties"
    except ValueError as e:
        # Should complain about a required property
        assert "required in type" in str(e)


# Property 3: Title validation enforces alphanumeric
@given(st.text())
def test_title_validation(title):
    """Test that resource titles must be alphanumeric"""
    # Check if the title is valid according to the regex
    import re
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    is_valid = bool(title and valid_names.match(title))
    
    try:
        # Create a minimal valid cluster
        cluster = pcs.Cluster(
            title,
            Networking=pcs.Networking(SubnetIds=["subnet-123"]),
            Scheduler=pcs.Scheduler(Type="SLURM", Version="23.11"),
            Size="SMALL"
        )
        # If we got here, title was accepted
        assert is_valid, f"Invalid title '{title}' was accepted"
    except ValueError as e:
        # Title was rejected
        assert not is_valid, f"Valid title '{title}' was rejected"
        assert "not alphanumeric" in str(e)


# Property 4: ScalingConfiguration min <= max invariant
@given(
    min_count=st.integers(min_value=0, max_value=1000),
    max_count=st.integers(min_value=0, max_value=1000)
)
def test_scaling_configuration_invariant(min_count, max_count):
    """Test ScalingConfiguration accepts any integer values for min and max"""
    # The code doesn't actually enforce min <= max, so this should always work
    config = pcs.ScalingConfiguration(
        MinInstanceCount=min_count,
        MaxInstanceCount=max_count
    )
    result = config.to_dict()
    assert result["MinInstanceCount"] == min_count
    assert result["MaxInstanceCount"] == max_count


# Property 5: JSON round-trip preservation
@composite
def valid_cluster_data(draw):
    """Generate valid cluster data for round-trip testing"""
    name = draw(st.text(string.ascii_letters + string.digits, min_size=1, max_size=20))
    subnet_ids = draw(st.lists(
        st.text(string.ascii_lowercase + string.digits, min_size=5, max_size=15),
        min_size=1, max_size=3
    ))
    scheduler_type = draw(st.sampled_from(["SLURM", "AWS_BATCH", "AWS_PCS"]))
    version = draw(st.text(string.digits + ".", min_size=1, max_size=10))
    size = draw(st.sampled_from(["SMALL", "MEDIUM", "LARGE"]))
    
    return {
        "name": name,
        "subnet_ids": subnet_ids,
        "scheduler_type": scheduler_type,
        "version": version,
        "size": size
    }


@given(valid_cluster_data())
def test_json_round_trip(data):
    """Test that objects survive to_dict() and from_dict() round-trip"""
    # Create a cluster
    original = pcs.Cluster(
        data["name"],
        Networking=pcs.Networking(SubnetIds=data["subnet_ids"]),
        Scheduler=pcs.Scheduler(Type=data["scheduler_type"], Version=data["version"]),
        Size=data["size"]
    )
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Convert back from dict (extract Properties)
    props = dict_repr.get("Properties", {})
    restored = pcs.Cluster.from_dict(data["name"], props)
    
    # Should be equal
    assert original == restored
    
    # Double-check specific properties
    assert restored.to_dict() == dict_repr


# Property 6: Property type enforcement
@given(
    st.one_of(
        st.integers(),
        st.floats(),
        st.dictionaries(st.text(), st.text()),
        st.booleans()
    )
)
def test_property_type_enforcement(invalid_value):
    """Test that property types are enforced"""
    # SubnetIds should be a list of strings
    try:
        networking = pcs.Networking(SubnetIds=invalid_value)
        # If it's not a list, it should have failed
        assert isinstance(invalid_value, list), f"Non-list value {invalid_value} was accepted for SubnetIds"
    except (TypeError, AttributeError) as e:
        # Expected for non-list types
        assert not isinstance(invalid_value, list)


# Property 7: Custom settings parameter validation
@given(
    param_name=st.text(),
    param_value=st.text()
)
def test_slurm_custom_setting_accepts_any_strings(param_name, param_value):
    """Test that SlurmCustomSetting accepts any string values"""
    setting = pcs.SlurmCustomSetting(
        ParameterName=param_name,
        ParameterValue=param_value
    )
    result = setting.to_dict()
    assert result["ParameterName"] == param_name
    assert result["ParameterValue"] == param_value


# Property 8: Empty vs None property handling
@given(st.booleans())
def test_optional_properties_handling(include_optional):
    """Test that optional properties can be omitted or included"""
    cluster_name = "TestCluster"
    
    kwargs = {
        "Networking": pcs.Networking(SubnetIds=["subnet-123"]),
        "Scheduler": pcs.Scheduler(Type="SLURM", Version="23.11"),
        "Size": "SMALL"
    }
    
    if include_optional:
        kwargs["Name"] = "OptionalName"
        kwargs["Tags"] = {"Environment": "Test"}
    
    cluster = pcs.Cluster(cluster_name, **kwargs)
    result = cluster.to_dict()
    
    props = result["Properties"]
    if include_optional:
        assert "Name" in props
        assert "Tags" in props
    else:
        # Optional properties should not appear if not set
        assert "Name" not in props
        assert "Tags" not in props
    
    # Required properties should always be present
    assert "Networking" in props
    assert "Scheduler" in props
    assert "Size" in props