"""More intensive property-based tests for troposphere.pinpoint module"""
import sys
import math
from hypothesis import given, strategies as st, assume, settings, example
import pytest

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.pinpoint as pinpoint
from troposphere.validators import boolean, integer, double


# More intensive test for edge cases in boolean validator
@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
@settings(max_examples=500)
def test_boolean_validator_edge_cases(value):
    """Test boolean validator with various edge cases"""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    try:
        result = boolean(value)
        # If it succeeds, value must be in one of the valid lists
        assert value in valid_true or value in valid_false
        if value in valid_true:
            assert result is True
        if value in valid_false:
            assert result is False
    except ValueError:
        # If it raises ValueError, value should not be in valid lists
        assert value not in valid_true and value not in valid_false


# Test very large coordinates
@given(
    latitude=st.floats(allow_nan=False, allow_infinity=False),
    longitude=st.floats(allow_nan=False, allow_infinity=False)
)
@settings(max_examples=500)
def test_coordinates_accepts_any_floats(latitude, longitude):
    """Test that Coordinates accepts any float values (no range validation)"""
    # The class uses double validator which just checks if it's convertible to float
    # It doesn't validate GPS coordinate ranges
    coords = pinpoint.Coordinates(
        Latitude=latitude,
        Longitude=longitude
    )
    
    assert coords.properties.get("Latitude") == latitude
    assert coords.properties.get("Longitude") == longitude


# Test integer validator with string representations
@given(st.text())
@settings(max_examples=500)
def test_integer_validator_string_parsing(value):
    """Test integer validator's string parsing behavior"""
    try:
        # Python's int() behavior is what we're testing against
        expected = int(value)
        result = integer(value)
        assert result == value  # Should return original value
    except (ValueError, TypeError):
        with pytest.raises(ValueError):
            integer(value)


# Test double validator with edge cases
@given(st.one_of(
    st.just(float('inf')),
    st.just(float('-inf')),
    st.just(float('nan')),
    st.floats()
))
@settings(max_examples=200)
def test_double_validator_special_floats(value):
    """Test double validator with special float values"""
    try:
        float_val = float(value)
        # double() should accept any value that float() accepts
        result = double(value)
        assert result == value
    except (ValueError, TypeError):
        with pytest.raises(ValueError):
            double(value)


# Test App class with Tags
@given(
    name=st.text(min_size=1, max_size=50),
    tags=st.one_of(
        st.none(),
        st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.text(min_size=0, max_size=20),
            min_size=0,
            max_size=5
        )
    )
)
@settings(max_examples=200)
def test_app_with_tags(name, tags):
    """Test App class with various tag configurations"""
    kwargs = {"Name": name}
    if tags is not None:
        kwargs["Tags"] = tags
    
    app = pinpoint.App(**kwargs)
    
    assert app.properties.get("Name") == name
    if tags is not None:
        assert app.properties.get("Tags") == tags
    
    # to_dict should work
    result = app.to_dict()
    assert result["Name"] == name
    if tags is not None:
        assert result["Tags"] == tags


# Test Message class with many optional properties
@given(
    action=st.one_of(st.none(), st.text(max_size=20)),
    body=st.one_of(st.none(), st.text(max_size=100)),
    title=st.one_of(st.none(), st.text(max_size=50)),
    url=st.one_of(st.none(), st.text(max_size=100)),
    silent_push=st.one_of(st.none(), st.booleans()),
    time_to_live=st.one_of(st.none(), st.integers(min_value=0, max_value=2592000))
)
@settings(max_examples=200)
def test_message_optional_properties(action, body, title, url, silent_push, time_to_live):
    """Test Message class with various optional properties"""
    kwargs = {}
    if action is not None:
        kwargs["Action"] = action
    if body is not None:
        kwargs["Body"] = body
    if title is not None:
        kwargs["Title"] = title
    if url is not None:
        kwargs["Url"] = url
    if silent_push is not None:
        kwargs["SilentPush"] = silent_push
    if time_to_live is not None:
        kwargs["TimeToLive"] = time_to_live
    
    message = pinpoint.Message(**kwargs)
    
    for key, value in kwargs.items():
        assert message.properties.get(key) == value
    
    # to_dict should work
    result = message.to_dict()
    for key, value in kwargs.items():
        if value is not None:
            assert key in result


# Test nested property structures
@given(
    lat=st.floats(min_value=-90, max_value=90, allow_nan=False),
    lon=st.floats(min_value=-180, max_value=180, allow_nan=False),
    range_km=st.floats(min_value=0.1, max_value=10000, allow_nan=False),
    country_values=st.lists(st.text(min_size=1, max_size=5), min_size=0, max_size=3)
)
@settings(max_examples=200)
def test_location_with_nested_properties(lat, lon, range_km, country_values):
    """Test Location class with nested GPSPoint and SetDimension"""
    coords = pinpoint.Coordinates(Latitude=lat, Longitude=lon)
    gps_point = pinpoint.GPSPoint(Coordinates=coords, RangeInKilometers=range_km)
    
    kwargs = {"GPSPoint": gps_point}
    
    if country_values:
        country_dim = pinpoint.SetDimension(Values=country_values)
        kwargs["Country"] = country_dim
    
    location = pinpoint.Location(**kwargs)
    
    assert location.properties.get("GPSPoint") == gps_point
    
    # Test serialization of nested structure
    result = location.to_dict()
    assert "GPSPoint" in result
    assert "Coordinates" in result["GPSPoint"]
    assert result["GPSPoint"]["Coordinates"]["Latitude"] == lat
    assert result["GPSPoint"]["Coordinates"]["Longitude"] == lon
    assert result["GPSPoint"]["RangeInKilometers"] == range_km
    
    if country_values:
        assert "Country" in result
        assert result["Country"]["Values"] == country_values


# Test Campaign required properties
@given(
    app_id=st.text(min_size=1, max_size=20),
    name=st.text(min_size=1, max_size=20),
    segment_id=st.text(min_size=1, max_size=20),
    frequency=st.sampled_from(["ONCE", "HOURLY", "DAILY", "WEEKLY", "MONTHLY"])
)
@settings(max_examples=100)
def test_campaign_required_properties(app_id, name, segment_id, frequency):
    """Test Campaign class with required properties"""
    schedule = pinpoint.Schedule(Frequency=frequency)
    
    campaign = pinpoint.Campaign(
        ApplicationId=app_id,
        Name=name,
        Schedule=schedule,
        SegmentId=segment_id
    )
    
    assert campaign.properties.get("ApplicationId") == app_id
    assert campaign.properties.get("Name") == name
    assert campaign.properties.get("SegmentId") == segment_id
    assert campaign.properties.get("Schedule") == schedule
    
    # to_dict should include all required properties
    result = campaign.to_dict()
    assert result["ApplicationId"] == app_id
    assert result["Name"] == name
    assert result["SegmentId"] == segment_id
    assert "Schedule" in result


if __name__ == "__main__":
    # Run with verbose output
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short", "-s"]))