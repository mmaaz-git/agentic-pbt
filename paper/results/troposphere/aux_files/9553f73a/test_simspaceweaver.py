import troposphere.simspaceweaver as ssw
from hypothesis import given, strategies as st, assume
import pytest


# Strategy for valid S3 bucket names (simplified AWS rules)
valid_bucket_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-.",
    min_size=3,
    max_size=63
).filter(lambda s: s[0].isalnum() and s[-1].isalnum() and ".." not in s)

# Strategy for valid S3 object keys
valid_object_key = st.text(min_size=1, max_size=1024).filter(
    lambda s: all(c not in s for c in ['\x00', '\r', '\n'])
)

# Strategy for valid ARNs
valid_arn = st.text(min_size=1).map(lambda s: f"arn:aws:iam::123456789012:role/{s}")

# Strategy for valid names
valid_name = st.text(
    alphabet=st.characters(blacklist_categories=["Cc", "Cs"]),
    min_size=1,
    max_size=255
)


@given(
    bucket_name=valid_bucket_name,
    object_key=valid_object_key
)
def test_s3location_round_trip(bucket_name, object_key):
    """Test that S3Location survives round-trip through to_dict/from_dict"""
    # Create S3Location
    original = ssw.S3Location(BucketName=bucket_name, ObjectKey=object_key)
    
    # Convert to dict
    d = original.to_dict()
    
    # Convert back from dict
    restored = ssw.S3Location.from_dict("TestTitle", d)
    
    # Check round-trip property
    assert restored.to_dict() == d
    assert restored.to_dict() == original.to_dict()


@given(
    title=valid_name,
    name=valid_name,
    role_arn=valid_arn,
    max_duration=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_simulation_round_trip(title, name, role_arn, max_duration):
    """Test that Simulation survives round-trip through to_dict/from_dict"""
    # Create Simulation
    kwargs = {"Name": name, "RoleArn": role_arn}
    if max_duration is not None:
        kwargs["MaximumDuration"] = max_duration
    
    original = ssw.Simulation(title, **kwargs)
    
    # Convert to dict
    d = original.to_dict()
    
    # Convert back from dict - this is expected to fail based on manual testing
    restored = ssw.Simulation.from_dict("NewTitle", d)
    
    # Check round-trip property
    assert restored.to_dict() == d


@given(
    bucket_name=valid_bucket_name,
    object_key=valid_object_key
)
def test_s3location_to_dict_structure(bucket_name, object_key):
    """Test that S3Location.to_dict() returns expected structure"""
    s3_loc = ssw.S3Location(BucketName=bucket_name, ObjectKey=object_key)
    d = s3_loc.to_dict()
    
    # Check expected keys exist
    assert "BucketName" in d
    assert "ObjectKey" in d
    assert d["BucketName"] == bucket_name
    assert d["ObjectKey"] == object_key
    assert len(d) == 2  # Should only have these two keys


@given(
    title=valid_name,
    name=valid_name,
    role_arn=valid_arn
)
def test_simulation_to_dict_structure(title, name, role_arn):
    """Test that Simulation.to_dict() returns expected structure"""
    sim = ssw.Simulation(title, Name=name, RoleArn=role_arn)
    d = sim.to_dict()
    
    # Check expected structure
    assert "Type" in d
    assert "Properties" in d
    assert d["Type"] == "AWS::SimSpaceWeaver::Simulation"
    assert isinstance(d["Properties"], dict)
    assert "Name" in d["Properties"]
    assert "RoleArn" in d["Properties"]
    assert d["Properties"]["Name"] == name
    assert d["Properties"]["RoleArn"] == role_arn


@given(
    bucket_name=st.one_of(
        st.integers(),
        st.floats(allow_nan=False),
        st.booleans(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    ),
    object_key=valid_object_key
)
def test_s3location_validation_wrong_type(bucket_name, object_key):
    """Test that S3Location validation catches type errors"""
    assume(not isinstance(bucket_name, str))  # Ensure it's not a string
    
    s3_loc = ssw.S3Location(BucketName=bucket_name, ObjectKey=object_key)
    
    # Validation should raise an error for wrong type
    with pytest.raises(TypeError) as exc_info:
        s3_loc.validate()
    
    assert "expected <class 'str'>" in str(exc_info.value)


@given(
    bucket_name=valid_bucket_name,
    object_key=valid_object_key,
    include_s3_loc=st.booleans()
)
def test_simulation_with_s3location(bucket_name, object_key, include_s3_loc):
    """Test Simulation with S3Location properties"""
    sim_kwargs = {
        "Name": "TestSim",
        "RoleArn": "arn:aws:iam::123456789012:role/SimRole"
    }
    
    if include_s3_loc:
        s3_loc = ssw.S3Location(BucketName=bucket_name, ObjectKey=object_key)
        sim_kwargs["SchemaS3Location"] = s3_loc
    
    sim = ssw.Simulation("MySimulation", **sim_kwargs)
    d = sim.to_dict()
    
    # Check structure
    assert "Properties" in d
    if include_s3_loc:
        assert "SchemaS3Location" in d["Properties"]
        assert d["Properties"]["SchemaS3Location"]["BucketName"] == bucket_name
        assert d["Properties"]["SchemaS3Location"]["ObjectKey"] == object_key


@given(
    bucket_name=valid_bucket_name
)
def test_s3location_missing_required_field(bucket_name):
    """Test that S3Location with missing required field can be created but not validated"""
    # Should be able to create without ObjectKey
    s3_loc = ssw.S3Location(BucketName=bucket_name)
    
    # to_dict should work but not include missing field
    d = s3_loc.to_dict()
    assert "BucketName" in d
    assert "ObjectKey" not in d
    
    # validate should not fail (based on observed behavior)
    s3_loc.validate()  # This passes - no exception raised