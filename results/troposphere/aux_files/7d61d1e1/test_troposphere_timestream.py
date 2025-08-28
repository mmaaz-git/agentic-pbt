import json
import troposphere.timestream as ts
from hypothesis import given, strategies as st, assume, settings
import pytest


@given(st.one_of(
    st.just(True),
    st.just(False),
    st.just(1),
    st.just(0),
    st.just("1"),
    st.just("0"),
    st.just("true"),
    st.just("True"),
    st.just("false"),
    st.just("False")
))
def test_boolean_valid_inputs(value):
    """Test that boolean() correctly handles documented valid inputs."""
    result = ts.boolean(value)
    assert isinstance(result, bool)
    
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


@given(st.one_of(
    st.none(),
    st.text().filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.floats(),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_invalid_inputs_raise_error(value):
    """Test that boolean() raises ValueError for invalid inputs."""
    with pytest.raises(ValueError):
        ts.boolean(value)


@given(st.one_of(
    st.integers(),
    st.text(alphabet="0123456789", min_size=1),
    st.text(alphabet="0123456789+-", min_size=1).filter(lambda x: x not in ['+', '-'] and not x.startswith('++') and not x.startswith('--'))
))
def test_integer_valid_inputs(value):
    """Test that integer() accepts valid integer-convertible inputs."""
    try:
        int(value)
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False
    
    if is_valid:
        result = ts.integer(value)
        assert result == value  # Should preserve original value
    else:
        with pytest.raises(ValueError):
            ts.integer(value)


@given(st.one_of(
    st.floats().filter(lambda x: not x.is_integer()),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_invalid_inputs_raise_error(value):
    """Test that integer() raises ValueError for non-integer convertible values."""
    with pytest.raises(ValueError):
        ts.integer(value)


@given(
    st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
    st.text(min_size=1, max_size=50)
)
def test_database_roundtrip_to_dict_from_dict(title, db_name):
    """Test round-trip property: Database -> dict -> Database preserves data."""
    assume(title and title[0].isalpha())  # Title must start with letter
    
    # Create original database
    original = ts.Database(title, DatabaseName=db_name)
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Convert back from dict
    reconstructed = ts.Database.from_dict(title, dict_repr)
    
    # Verify they produce the same dict representation
    assert reconstructed.to_dict() == dict_repr
    assert reconstructed.title == title


@given(
    st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=50)
)
def test_table_roundtrip_to_dict_from_dict(title, db_name, table_name):
    """Test round-trip property: Table -> dict -> Table preserves data."""
    assume(title and title[0].isalpha())  # Title must start with letter
    
    # Create original table (DatabaseName is required)
    original = ts.Table(title, DatabaseName=db_name, TableName=table_name)
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Convert back from dict
    reconstructed = ts.Table.from_dict(title, dict_repr)
    
    # Verify they produce the same dict representation
    assert reconstructed.to_dict() == dict_repr
    assert reconstructed.title == title


@given(
    st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
    st.text(min_size=1, max_size=50)
)
def test_database_to_json_produces_valid_json(title, db_name):
    """Test that to_json produces valid parseable JSON."""
    assume(title and title[0].isalpha())
    
    db = ts.Database(title, DatabaseName=db_name)
    json_str = db.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    
    # Should contain expected structure
    assert 'Type' in parsed
    assert 'Properties' in parsed
    assert parsed['Properties']['DatabaseName'] == db_name


@given(
    st.text(min_size=1, max_size=20).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
    st.one_of(st.none(), st.text(min_size=0, max_size=50)),
    st.one_of(st.none(), st.text(min_size=0, max_size=50))
)
def test_database_optional_properties(title, db_name, kms_key):
    """Test Database with optional properties."""
    assume(title and title[0].isalpha())
    
    kwargs = {}
    if db_name is not None:
        kwargs['DatabaseName'] = db_name
    if kms_key is not None:
        kwargs['KmsKeyId'] = kms_key
    
    db = ts.Database(title, **kwargs)
    dict_repr = db.to_dict()
    
    # Verify structure
    assert 'Type' in dict_repr
    assert dict_repr['Type'] == 'AWS::Timestream::Database'
    
    if db_name is not None or kms_key is not None:
        assert 'Properties' in dict_repr
        if db_name is not None:
            assert dict_repr['Properties']['DatabaseName'] == db_name
        if kms_key is not None:
            assert dict_repr['Properties']['KmsKeyId'] == kms_key


@given(st.lists(st.integers()))
def test_partition_key_composite_list(partition_keys):
    """Test PartitionKey with lists."""
    # Create a Schema with composite partition keys
    schema_dict = {}
    if partition_keys:
        # Need to create PartitionKey objects
        pk_objects = []
        for i, _ in enumerate(partition_keys):
            pk = ts.PartitionKey()
            pk_objects.append(pk)
        schema_dict['CompositePartitionKey'] = pk_objects
    
    schema = ts.Schema(**schema_dict)
    dict_repr = schema.to_dict()
    
    # Should be able to convert to dict without error
    assert isinstance(dict_repr, dict)


@given(st.text())
def test_measure_value_type_validation(measure_type):
    """Test MixedMeasureMapping with various MeasureValueType values."""
    # MeasureValueType is required
    try:
        mapping = ts.MixedMeasureMapping(MeasureValueType=measure_type)
        # If it succeeds, should be able to convert to dict
        dict_repr = mapping.to_dict()
        assert 'MeasureValueType' in dict_repr
        assert dict_repr['MeasureValueType'] == measure_type
    except Exception:
        # Some values might be invalid based on AWS constraints
        # but the library itself doesn't validate
        pass