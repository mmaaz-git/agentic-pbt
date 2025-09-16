import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import troposphere.location as location
from troposphere.validators import boolean


# Test 1: Boolean validator transformation property
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_validator_known_values(value):
    """Test that boolean validator handles all documented true/false values correctly"""
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_validator_invalid_values(value):
    """Test that boolean validator raises ValueError for invalid inputs"""
    with pytest.raises(ValueError):
        boolean(value)


# Test 2: Round-trip property for from_dict/to_dict
@composite
def valid_apikey_dict(draw):
    """Generate valid APIKey dictionaries"""
    data = {
        "KeyName": draw(st.text(min_size=1, max_size=100)),
        "Restrictions": {
            "AllowActions": draw(st.lists(st.text(min_size=1), min_size=1, max_size=10)),
            "AllowResources": draw(st.lists(st.text(min_size=1), min_size=1, max_size=10))
        }
    }
    # Add optional fields sometimes
    if draw(st.booleans()):
        data["Description"] = draw(st.text(min_size=1, max_size=200))
    if draw(st.booleans()):
        data["ForceDelete"] = draw(st.booleans())
    if draw(st.booleans()):
        data["ForceUpdate"] = draw(st.booleans())
    if draw(st.booleans()):
        data["NoExpiry"] = draw(st.booleans())
    return data


@given(valid_apikey_dict())
@settings(max_examples=100)
def test_apikey_roundtrip_from_dict_to_dict(data):
    """Test that APIKey.from_dict(d).to_dict() preserves data"""
    obj = location.APIKey.from_dict("TestKey", data)
    result = obj.to_dict(validation=False)
    
    # Check required fields are preserved
    assert result["Properties"]["KeyName"] == data["KeyName"]
    assert result["Properties"]["Restrictions"]["AllowActions"] == data["Restrictions"]["AllowActions"]
    assert result["Properties"]["Restrictions"]["AllowResources"] == data["Restrictions"]["AllowResources"]
    
    # Check optional fields if present
    if "Description" in data:
        assert result["Properties"]["Description"] == data["Description"]
    if "ForceDelete" in data:
        assert result["Properties"]["ForceDelete"] == data["ForceDelete"]


@composite  
def valid_geofence_dict(draw):
    """Generate valid GeofenceCollection dictionaries"""
    data = {
        "CollectionName": draw(st.text(min_size=1, max_size=100))
    }
    if draw(st.booleans()):
        data["Description"] = draw(st.text(min_size=1, max_size=200))
    if draw(st.booleans()):
        data["KmsKeyId"] = draw(st.text(min_size=1, max_size=100))
    return data


@given(valid_geofence_dict())
@settings(max_examples=100)
def test_geofence_roundtrip(data):
    """Test GeofenceCollection round-trip property"""
    obj = location.GeofenceCollection.from_dict("TestGeofence", data)
    result = obj.to_dict(validation=False)
    
    assert result["Properties"]["CollectionName"] == data["CollectionName"]
    if "Description" in data:
        assert result["Properties"]["Description"] == data["Description"]
    if "KmsKeyId" in data:
        assert result["Properties"]["KmsKeyId"] == data["KmsKeyId"]


# Test 3: Property validation - required vs optional fields
@given(st.dictionaries(
    st.sampled_from(["Description", "ExpireTime", "ForceDelete", "ForceUpdate", "NoExpiry"]),
    st.one_of(st.text(), st.booleans())
))
def test_apikey_missing_required_fields(optional_fields):
    """Test that APIKey validation fails when required fields are missing"""
    # Create dict with only optional fields (missing required KeyName and Restrictions)
    with pytest.raises((TypeError, KeyError, AttributeError)):
        obj = location.APIKey.from_dict("TestKey", optional_fields)
        obj.validate()


@given(st.text(min_size=1, max_size=100))
def test_geofence_with_only_required_field(collection_name):
    """Test that GeofenceCollection works with only required CollectionName"""
    data = {"CollectionName": collection_name}
    obj = location.GeofenceCollection.from_dict("TestGeofence", data)
    result = obj.to_dict(validation=False)
    assert result["Properties"]["CollectionName"] == collection_name
    assert result["Type"] == "AWS::Location::GeofenceCollection"


@composite
def valid_map_dict(draw):
    """Generate valid Map dictionaries"""
    data = {
        "MapName": draw(st.text(min_size=1, max_size=100)),
        "Configuration": {
            "Style": draw(st.text(min_size=1, max_size=50))
        }
    }
    if draw(st.booleans()):
        data["Description"] = draw(st.text(min_size=1, max_size=200))
    if draw(st.booleans()):
        data["Configuration"]["PoliticalView"] = draw(st.text(min_size=1, max_size=50))
    return data


@given(valid_map_dict())
@settings(max_examples=100)
def test_map_roundtrip(data):
    """Test Map round-trip property"""
    obj = location.Map.from_dict("TestMap", data)
    result = obj.to_dict(validation=False)
    
    assert result["Properties"]["MapName"] == data["MapName"]
    assert result["Properties"]["Configuration"]["Style"] == data["Configuration"]["Style"]
    if "Description" in data:
        assert result["Properties"]["Description"] == data["Description"]


# Test idempotence property of to_dict
@given(valid_apikey_dict())
def test_to_dict_idempotent(data):
    """Test that calling to_dict multiple times produces the same result"""
    obj = location.APIKey.from_dict("TestKey", data)
    result1 = obj.to_dict(validation=False)
    result2 = obj.to_dict(validation=False)
    assert result1 == result2


# Test that validation doesn't modify the object
@given(valid_geofence_dict())
def test_validate_doesnt_modify(data):
    """Test that validate() doesn't modify the object"""
    obj = location.GeofenceCollection.from_dict("TestGeofence", data)
    dict_before = obj.to_dict(validation=False)
    try:
        obj.validate()
    except:
        pass  # Validation might fail, that's ok
    dict_after = obj.to_dict(validation=False)
    assert dict_before == dict_after


# Test consistency between validation parameter
@given(valid_map_dict())
def test_to_dict_validation_parameter(data):
    """Test that to_dict with validation=True validates the object"""
    obj = location.Map.from_dict("TestMap", data)
    # This should succeed without raising if validation passes
    result_with_validation = obj.to_dict(validation=True)
    result_without_validation = obj.to_dict(validation=False)
    # The structure should be the same regardless of validation
    assert result_with_validation.keys() == result_without_validation.keys()