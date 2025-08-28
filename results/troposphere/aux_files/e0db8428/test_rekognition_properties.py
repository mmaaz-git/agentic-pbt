import math
from hypothesis import given, strategies as st, assume
import troposphere.rekognition as rek


# Test 1: validate_PolygonRegionsOfInterest crashes due to missing Point class
@given(st.lists(st.lists(st.integers())))
def test_validate_polygon_regions_crashes(polygons):
    """Test that validate_PolygonRegionsOfInterest always crashes due to missing Point class"""
    try:
        rek.validate_PolygonRegionsOfInterest(polygons)
        assert False, "Expected ImportError but validation succeeded"
    except ImportError as e:
        assert "cannot import name 'Point'" in str(e)
    except TypeError:
        # This is expected for invalid input types
        pass


# Test 2: StreamProcessor.PolygonRegionsOfInterest property crashes when set
@given(st.lists(st.lists(st.lists(st.floats(allow_nan=False, allow_infinity=False)))))
def test_streamprocessor_polygon_regions_crashes(polygon_data):
    """Test that setting PolygonRegionsOfInterest on StreamProcessor crashes"""
    sp = rek.StreamProcessor('TestProcessor')
    sp.RoleArn = 'arn:aws:iam::123456789012:role/TestRole'
    
    try:
        sp.PolygonRegionsOfInterest = polygon_data
        sp.to_dict()  # This triggers validation
        assert False, "Expected ImportError but succeeded"
    except ImportError as e:
        assert "cannot import name 'Point'" in str(e)
    except (TypeError, AttributeError):
        # Other validation errors are expected for invalid data
        pass


# Test 3: BoundingBox to_dict/from_dict round-trip property
@given(
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
)
def test_boundingbox_round_trip(height, width, left, top):
    """Test that BoundingBox survives to_dict/from_dict round-trip"""
    bb = rek.BoundingBox()
    bb.Height = height
    bb.Width = width
    bb.Left = left
    bb.Top = top
    
    dict_repr = bb.to_dict()
    bb_restored = rek.BoundingBox.from_dict('TestBB', dict_repr)
    dict_restored = bb_restored.to_dict()
    
    assert math.isclose(dict_repr['Height'], dict_restored['Height'])
    assert math.isclose(dict_repr['Width'], dict_restored['Width'])
    assert math.isclose(dict_repr['Left'], dict_restored['Left'])
    assert math.isclose(dict_repr['Top'], dict_restored['Top'])


# Test 4: double function handles numeric strings
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_double_string_round_trip(value):
    """Test that double function correctly handles string representations"""
    str_value = str(value)
    result = rek.double(str_value)
    assert math.isclose(result, value, rel_tol=1e-9, abs_tol=1e-10)


# Test 5: boolean function handles various truthy/falsy values
@given(st.one_of(
    st.booleans(),
    st.integers(min_value=0, max_value=1),
    st.sampled_from(['true', 'false', 'True', 'False', 'TRUE', 'FALSE'])
))
def test_boolean_conversion(value):
    """Test that boolean function correctly converts various inputs"""
    result = rek.boolean(value)
    assert isinstance(result, bool)
    
    # Check expected conversions
    if value in [True, 1, 'true', 'True', 'TRUE']:
        assert result is True
    elif value in [False, 0, 'false', 'False', 'FALSE']:
        assert result is False


# Test 6: Collection to_dict includes required Type field
@given(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
def test_collection_type_field(collection_id):
    """Test that Collection.to_dict always includes the Type field"""
    col = rek.Collection('TestCollection')
    col.CollectionId = collection_id
    
    result = col.to_dict()
    assert 'Type' in result
    assert result['Type'] == 'AWS::Rekognition::Collection'
    assert 'Properties' in result
    assert result['Properties']['CollectionId'] == collection_id


# Test 7: Test typo in error message
def test_validate_polygon_error_message_typo():
    """Test that the error message contains a typo 'ponts' instead of 'points'"""
    # We need to patch the import to make the function work past the Point import
    import sys
    import types
    
    # Create a fake Point class
    point_module = types.ModuleType('fake_point')
    
    class FakePoint:
        pass
    
    # Temporarily add to rekognition module
    original_point = getattr(rek, 'Point', None)
    rek.Point = FakePoint
    
    try:
        # Now test the typo in the error message
        rek.validate_PolygonRegionsOfInterest([['not points']])
    except TypeError as e:
        assert 'ponts' in str(e), f"Expected typo 'ponts' in error message, got: {e}"
        assert 'points' not in str(e), f"Expected typo but got correct spelling: {e}"
    finally:
        # Restore original state
        if original_point is None:
            delattr(rek, 'Point')
        else:
            rek.Point = original_point