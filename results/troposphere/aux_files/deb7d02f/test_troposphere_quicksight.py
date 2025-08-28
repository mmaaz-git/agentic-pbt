import random
import string
from datetime import datetime

import pytest
from hypothesis import assume, given, settings, strategies as st

import troposphere.quicksight as qs


# Test 1: Boolean validator property
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.text(),
    st.integers(),
    st.floats(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_boolean_validator_consistent(value):
    """Test that boolean validator accepts valid boolean representations and rejects invalid ones."""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    if value in valid_true:
        result = qs.boolean(value)
        assert result is True, f"boolean({value!r}) should return True"
    elif value in valid_false:
        result = qs.boolean(value)
        assert result is False, f"boolean({value!r}) should return False"
    else:
        with pytest.raises(ValueError):
            qs.boolean(value)


# Test 2: Double validator property
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(alphabet=string.digits + ".-+eE", min_size=1),
    st.text(),
    st.sampled_from(["3.14", "-2.5", "1e10", "0", "-0"]),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_double_validator_float_conversion(value):
    """Test that double validator accepts values convertible to float and rejects others."""
    try:
        # Try the same conversion that double() would do
        float(value)
        expected_valid = True
    except (ValueError, TypeError):
        expected_valid = False
    
    if expected_valid:
        result = qs.double(value)
        # Should return the original value unchanged
        assert result == value, f"double({value!r}) should return {value!r}"
    else:
        with pytest.raises(ValueError):
            qs.double(value)


# Test 3: Round-trip property for double validator
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.sampled_from(["3.14", "-2.5", "1e10", "0"])
))
def test_double_validator_preserves_valid_input(value):
    """Test that double validator preserves valid numeric inputs unchanged."""
    try:
        float(value)  # Ensure it's convertible
        result = qs.double(value)
        assert result == value, f"double({value!r}) should preserve the input"
    except (ValueError, TypeError):
        pass  # Skip invalid values


# Test 4: Round-trip property for AWSProperty classes
@given(
    resize_option=st.sampled_from(["FIXED", "RESPONSIVE"]),
    viewport_width=st.one_of(st.none(), st.text(min_size=1, max_size=10))
)
def test_aws_property_round_trip(resize_option, viewport_width):
    """Test that from_dict(to_dict(obj)) preserves object data."""
    # Create an object with the given properties
    kwargs = {"ResizeOption": resize_option}
    if viewport_width is not None:
        kwargs["OptimizedViewPortWidth"] = viewport_width
    
    # Create object via constructor
    obj1 = qs.GridLayoutScreenCanvasSizeOptions(**kwargs)
    
    # Convert to dict and back
    dict_repr = obj1.to_dict()
    obj2 = qs.GridLayoutScreenCanvasSizeOptions.from_dict("TestObject", dict_repr)
    dict_repr2 = obj2.to_dict()
    
    # The dictionary representations should be identical
    assert dict_repr == dict_repr2, f"Round-trip failed: {dict_repr} != {dict_repr2}"


# Test 5: Multiple AWS classes round-trip property
@given(
    class_idx=st.integers(min_value=0, max_value=10),
    data=st.dictionaries(
        st.sampled_from(["Prop1", "Prop2", "OptionalProp"]),
        st.text(min_size=1, max_size=20),
        min_size=1
    )
)
def test_multiple_aws_classes_round_trip(class_idx, data):
    """Test round-trip property for multiple AWS classes."""
    # Sample some classes that have simple string properties
    test_classes = [
        qs.AggregationFunction,
        qs.AnchorDateConfiguration, 
        qs.ArcAxisDisplayRange,
        qs.AssetOptions,
        qs.AxisDisplayRange,
        qs.AxisLabelOptions,
        qs.ChartAxisLabelOptions,
        qs.ColorScale,
        qs.ColumnIdentifier,
        qs.ConditionalFormattingColor,
        qs.ContributionAnalysisDefault
    ]
    
    cls = test_classes[class_idx % len(test_classes)]
    
    # Try to create object from dict (may fail if required props missing)
    try:
        obj1 = cls.from_dict("TestObj", data)
        dict1 = obj1.to_dict(validation=False)  # Skip validation for this test
        obj2 = cls.from_dict("TestObj2", dict1)
        dict2 = obj2.to_dict(validation=False)
        
        assert dict1 == dict2, f"Round-trip failed for {cls.__name__}: {dict1} != {dict2}"
    except (TypeError, KeyError, AttributeError):
        # Some classes may have required properties or complex structures
        pass


# Test 6: Validation of required properties
@given(
    include_required=st.booleans(),
    include_optional=st.booleans()
)
def test_required_property_validation(include_required, include_optional):
    """Test that classes with required properties validate correctly."""
    # GridLayoutScreenCanvasSizeOptions has ResizeOption as required
    kwargs = {}
    if include_required:
        kwargs["ResizeOption"] = "FIXED"
    if include_optional:
        kwargs["OptimizedViewPortWidth"] = "1200"
    
    obj = qs.GridLayoutScreenCanvasSizeOptions(**kwargs)
    
    if include_required:
        # Should succeed validation if required prop is present
        obj.to_dict()
    else:
        # Should fail validation if required property missing
        with pytest.raises(ValueError, match="required"):
            obj.to_dict()


# Test 7: Property name validation
@given(
    prop_name=st.text(alphabet=string.ascii_letters + string.digits + "_-", min_size=1),
    prop_value=st.text()
)
def test_property_name_validation(prop_name, prop_value):
    """Test that only valid property names are accepted."""
    valid_props = {"ResizeOption", "OptimizedViewPortWidth"}
    
    kwargs = {prop_name: prop_value}
    if prop_name == "ResizeOption":
        # This is valid, should work
        obj = qs.GridLayoutScreenCanvasSizeOptions(**kwargs)
        result = obj.to_dict(validation=False)
        assert prop_name in result
    elif prop_name not in valid_props:
        # Invalid property name
        with pytest.raises((TypeError, AttributeError, KeyError)):
            qs.GridLayoutScreenCanvasSizeOptions(**kwargs)


# Test 8: Nested property structures round-trip
@given(
    paper_margin_data=st.dictionaries(
        st.sampled_from(["Top", "Bottom", "Left", "Right"]),
        st.text(min_size=1, max_size=10),
        min_size=0,
        max_size=4
    )
)
def test_nested_property_round_trip(paper_margin_data):
    """Test round-trip for nested property structures like Spacing."""
    # Create a Spacing object
    spacing = qs.Spacing(**paper_margin_data)
    
    # Round-trip test
    dict1 = spacing.to_dict()
    spacing2 = qs.Spacing.from_dict("TestSpacing", dict1)
    dict2 = spacing2.to_dict()
    
    assert dict1 == dict2, f"Nested round-trip failed: {dict1} != {dict2}"


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])