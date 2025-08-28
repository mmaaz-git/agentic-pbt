"""Property-based tests for troposphere.pinpoint module"""
import sys
import math
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.pinpoint as pinpoint
from troposphere.validators import boolean, integer, double


# Test 1: Boolean validator property - documented conversions
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_documented_values(value):
    """Test that boolean validator correctly handles all documented values"""
    result = boolean(value)
    
    # Property: Values that should be True
    if value in [True, 1, "1", "true", "True"]:
        assert result is True, f"Expected True for {value}, got {result}"
    
    # Property: Values that should be False
    if value in [False, 0, "0", "false", "False"]:
        assert result is False, f"Expected False for {value}, got {result}"


# Test 2: Boolean validator idempotence
@given(st.booleans())
def test_boolean_validator_idempotence(value):
    """Test that boolean(boolean(x)) == boolean(x) for valid inputs"""
    result1 = boolean(value)
    result2 = boolean(result1)
    assert result1 == result2, f"boolean not idempotent: {result1} != {result2}"


# Test 3: Integer validator property
@given(st.one_of(
    st.integers(),
    st.text(alphabet="0123456789", min_size=1, max_size=10),
    st.text(alphabet="-0123456789", min_size=1, max_size=10).filter(lambda x: x != "-")
))
def test_integer_validator_valid_inputs(value):
    """Test that integer validator accepts valid integer representations"""
    try:
        int_val = int(value)  # Can this be converted to int?
        result = integer(value)
        # Property: integer() should return the same value for valid inputs
        assert result == value
    except (ValueError, TypeError):
        # If int() fails, integer() should also fail
        with pytest.raises(ValueError):
            integer(value)


# Test 4: Double validator property
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(alphabet="0123456789.", min_size=1, max_size=10).filter(
        lambda x: x.count('.') <= 1 and x != '.' and not x.startswith('.') and not x.endswith('.')
    )
))
def test_double_validator_valid_inputs(value):
    """Test that double validator accepts valid float representations"""
    try:
        float_val = float(value)  # Can this be converted to float?
        if not math.isnan(float_val) and not math.isinf(float_val):
            result = double(value)
            # Property: double() should return the same value for valid inputs
            assert result == value
    except (ValueError, TypeError):
        # If float() fails, double() should also fail
        with pytest.raises(ValueError):
            double(value)


# Test 5: Coordinates class property - accepts valid GPS coordinates
@given(
    latitude=st.floats(min_value=-90.0, max_value=90.0, allow_nan=False),
    longitude=st.floats(min_value=-180.0, max_value=180.0, allow_nan=False)
)
def test_coordinates_valid_gps_values(latitude, longitude):
    """Test that Coordinates class accepts valid GPS coordinate values"""
    # Property: Valid GPS coordinates should be accepted
    coords = pinpoint.Coordinates(
        Latitude=latitude,
        Longitude=longitude
    )
    
    # The object should be created successfully
    assert coords is not None
    assert coords.properties.get("Latitude") == latitude
    assert coords.properties.get("Longitude") == longitude
    
    # to_dict should work without errors
    result = coords.to_dict()
    assert "Latitude" in result
    assert "Longitude" in result


# Test 6: Limits class integer validation
@given(
    daily=st.one_of(st.none(), st.integers(min_value=0, max_value=1000000)),
    max_duration=st.one_of(st.none(), st.integers(min_value=0, max_value=1000000)),
    messages_per_second=st.one_of(st.none(), st.integers(min_value=0, max_value=1000000)),
    session=st.one_of(st.none(), st.integers(min_value=0, max_value=1000000)),
    total=st.one_of(st.none(), st.integers(min_value=0, max_value=1000000))
)
def test_limits_integer_properties(daily, max_duration, messages_per_second, session, total):
    """Test that Limits class properly validates integer properties"""
    kwargs = {}
    if daily is not None:
        kwargs["Daily"] = daily
    if max_duration is not None:
        kwargs["MaximumDuration"] = max_duration
    if messages_per_second is not None:
        kwargs["MessagesPerSecond"] = messages_per_second
    if session is not None:
        kwargs["Session"] = session
    if total is not None:
        kwargs["Total"] = total
    
    # Property: Valid integers should be accepted
    limits = pinpoint.Limits(**kwargs)
    
    # Verify properties were set correctly
    for key, value in kwargs.items():
        assert limits.properties.get(key) == value
    
    # to_dict should work
    result = limits.to_dict()
    for key, value in kwargs.items():
        if value is not None:
            assert key in result


# Test 7: QuietTime required properties
@given(
    start=st.text(min_size=1, max_size=10),
    end=st.text(min_size=1, max_size=10)
)
def test_quiet_time_required_properties(start, end):
    """Test that QuietTime requires both Start and End properties"""
    # Property: QuietTime should accept any string for Start and End
    quiet_time = pinpoint.QuietTime(
        Start=start,
        End=end
    )
    
    assert quiet_time.properties.get("Start") == start
    assert quiet_time.properties.get("End") == end
    
    # to_dict should include both properties
    result = quiet_time.to_dict()
    assert result["Start"] == start
    assert result["End"] == end


# Test 8: SetDimension Values property
@given(
    dimension_type=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    values=st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5))
)
def test_set_dimension_values_list(dimension_type, values):
    """Test that SetDimension properly handles Values as a list"""
    kwargs = {}
    if dimension_type is not None:
        kwargs["DimensionType"] = dimension_type
    if values is not None:
        kwargs["Values"] = values
    
    # Property: SetDimension should accept lists for Values
    set_dim = pinpoint.SetDimension(**kwargs)
    
    if values is not None:
        assert set_dim.properties.get("Values") == values
        # Verify it's stored as a list
        assert isinstance(set_dim.properties.get("Values"), list)


# Test 9: Test property validation for invalid types
@given(st.one_of(
    st.dictionaries(st.text(), st.text()),
    st.lists(st.integers()),
    st.tuples(st.integers(), st.integers())
))
def test_coordinates_rejects_invalid_types(invalid_value):
    """Test that Coordinates rejects non-numeric types for lat/long"""
    # Property: Non-numeric values should be rejected
    with pytest.raises((TypeError, ValueError)):
        pinpoint.Coordinates(
            Latitude=invalid_value,
            Longitude=0.0
        )
    
    with pytest.raises((TypeError, ValueError)):
        pinpoint.Coordinates(
            Latitude=0.0,
            Longitude=invalid_value
        )


# Test 10: GPSPoint with Coordinates composition
@given(
    latitude=st.floats(min_value=-90.0, max_value=90.0, allow_nan=False),
    longitude=st.floats(min_value=-180.0, max_value=180.0, allow_nan=False),
    range_km=st.floats(min_value=0.1, max_value=10000.0, allow_nan=False)
)
def test_gps_point_with_coordinates(latitude, longitude, range_km):
    """Test that GPSPoint properly composes with Coordinates"""
    # Create Coordinates object
    coords = pinpoint.Coordinates(
        Latitude=latitude,
        Longitude=longitude
    )
    
    # Property: GPSPoint should accept Coordinates object
    gps_point = pinpoint.GPSPoint(
        Coordinates=coords,
        RangeInKilometers=range_km
    )
    
    assert gps_point.properties.get("Coordinates") == coords
    assert gps_point.properties.get("RangeInKilometers") == range_km
    
    # to_dict should properly serialize nested structure
    result = gps_point.to_dict()
    assert "Coordinates" in result
    assert "RangeInKilometers" in result
    assert isinstance(result["Coordinates"], dict)
    assert result["Coordinates"]["Latitude"] == latitude
    assert result["Coordinates"]["Longitude"] == longitude


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))