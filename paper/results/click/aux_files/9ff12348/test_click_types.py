import math
import uuid as uuid_module
from datetime import datetime
from hypothesis import assume, given, strategies as st, settings
import click.types


@given(st.lists(st.text()))
def test_choice_normalization_unique(choices):
    """Test that Choice type normalization produces unique values for unique choices"""
    assume(len(choices) > 0)
    assume(len(set(choices)) == len(choices))
    
    choice_type = click.types.Choice(choices, case_sensitive=True)
    normalized = choice_type._normalized_mapping(ctx=None)
    
    assert len(normalized) == len(choices)
    assert len(set(normalized.values())) == len(choices)


@given(st.lists(st.text(min_size=1)))
def test_choice_convert_idempotence(choices):
    """Test that converting a valid choice twice returns the same value"""
    assume(len(choices) > 0)
    assume(len(set(choices)) == len(choices))
    
    choice_type = click.types.Choice(choices, case_sensitive=True)
    
    for choice in choices:
        converted_once = choice_type.convert(choice, None, None)
        converted_twice = choice_type.convert(converted_once, None, None)
        assert converted_once == converted_twice


@given(st.integers(), st.integers())
def test_int_range_bounds_invariant(min_val, max_val):
    """Test that IntRange always respects its bounds"""
    assume(min_val < max_val)
    
    int_range = click.types.IntRange(min=min_val, max=max_val)
    
    test_value = (min_val + max_val) // 2
    result = int_range.convert(test_value, None, None)
    
    assert min_val <= result <= max_val


@given(st.integers(), st.integers(), st.integers())
def test_int_range_clamp_property(min_val, max_val, test_val):
    """Test that clamping always produces values within bounds"""
    assume(min_val < max_val)
    
    int_range = click.types.IntRange(min=min_val, max=max_val, clamp=True)
    result = int_range.convert(test_val, None, None)
    
    assert min_val <= result <= max_val
    
    if test_val < min_val:
        assert result == min_val
    elif test_val > max_val:
        assert result == max_val
    else:
        assert result == test_val


@given(st.floats(allow_nan=False, allow_infinity=False),
       st.floats(allow_nan=False, allow_infinity=False))
def test_float_range_bounds_invariant(min_val, max_val):
    """Test that FloatRange always respects its bounds"""
    assume(min_val < max_val)
    assume(abs(max_val - min_val) < 1e10)
    
    float_range = click.types.FloatRange(min=min_val, max=max_val)
    
    test_value = (min_val + max_val) / 2
    result = float_range.convert(test_value, None, None)
    
    assert min_val <= result <= max_val


@given(st.floats(allow_nan=False, allow_infinity=False),
       st.floats(allow_nan=False, allow_infinity=False),
       st.floats(allow_nan=False, allow_infinity=False))
def test_float_range_clamp_property(min_val, max_val, test_val):
    """Test that float clamping always produces values within bounds"""
    assume(min_val < max_val)
    assume(abs(max_val - min_val) < 1e10)
    
    float_range = click.types.FloatRange(min=min_val, max=max_val, clamp=True)
    result = float_range.convert(test_val, None, None)
    
    assert min_val <= result <= max_val
    
    if test_val < min_val:
        assert math.isclose(result, min_val)
    elif test_val > max_val:
        assert math.isclose(result, max_val)
    else:
        assert math.isclose(result, test_val)


@given(st.text())
def test_string_type_idempotence(text):
    """Test that converting a string twice gives the same result"""
    string_type = click.types.StringParamType()
    
    converted_once = string_type.convert(text, None, None)
    converted_twice = string_type.convert(converted_once, None, None)
    
    assert converted_once == converted_twice
    assert isinstance(converted_once, str)


@given(st.integers())
def test_int_type_idempotence(value):
    """Test that converting an int twice gives the same result"""
    int_type = click.types.IntParamType()
    
    converted_once = int_type.convert(value, None, None)
    converted_twice = int_type.convert(converted_once, None, None)
    
    assert converted_once == converted_twice
    assert converted_once == value


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_float_type_idempotence(value):
    """Test that converting a float twice gives the same result"""
    float_type = click.types.FloatParamType()
    
    converted_once = float_type.convert(value, None, None)
    converted_twice = float_type.convert(converted_once, None, None)
    
    assert math.isclose(converted_once, converted_twice)
    assert math.isclose(converted_once, value)


@given(st.text())
def test_uuid_type_round_trip(text):
    """Test UUID type round-trip conversion"""
    uuid_type = click.types.UUIDParameterType()
    
    try:
        test_uuid = uuid_module.UUID(text)
    except ValueError:
        return
    
    converted = uuid_type.convert(text, None, None)
    assert isinstance(converted, uuid_module.UUID)
    assert str(converted) == str(test_uuid)
    
    converted_again = uuid_type.convert(converted, None, None)
    assert converted == converted_again


@given(st.lists(st.text()))
def test_choice_case_insensitive_normalization(choices):
    """Test case-insensitive choice normalization"""
    assume(len(choices) > 0)
    assume(all(c.strip() for c in choices))
    
    lower_choices = [c.lower() for c in choices]
    assume(len(set(lower_choices)) == len(lower_choices))
    
    choice_type = click.types.Choice(choices, case_sensitive=False)
    
    for choice in choices:
        upper_choice = choice.upper()
        lower_choice = choice.lower()
        mixed_choice = ''.join(c.upper() if i % 2 else c.lower() 
                               for i, c in enumerate(choice))
        
        original = choice_type.convert(choice, None, None)
        from_upper = choice_type.convert(upper_choice, None, None)
        from_lower = choice_type.convert(lower_choice, None, None)
        from_mixed = choice_type.convert(mixed_choice, None, None)
        
        assert original == from_upper == from_lower == from_mixed


@given(st.integers(min_value=-1000, max_value=1000))
def test_int_range_open_bounds(value):
    """Test open bounds behavior for IntRange"""
    min_val = 0
    max_val = 100
    
    range_closed = click.types.IntRange(min=min_val, max=max_val)
    range_min_open = click.types.IntRange(min=min_val, max=max_val, min_open=True)
    range_max_open = click.types.IntRange(min=min_val, max=max_val, max_open=True)
    
    if value == min_val:
        result = range_closed.convert(value, None, None)
        assert result == min_val
        
        try:
            range_min_open.convert(value, None, None)
            assert False, "Should have failed for min boundary with min_open=True"
        except click.types.BadParameter:
            pass
    
    if value == max_val:
        result = range_closed.convert(value, None, None)
        assert result == max_val
        
        try:
            range_max_open.convert(value, None, None)
            assert False, "Should have failed for max boundary with max_open=True"
        except click.types.BadParameter:
            pass


@given(st.integers())
def test_int_range_clamp_open_bounds(value):
    """Test clamping with open bounds for IntRange"""
    min_val = 0
    max_val = 100
    
    range_min_open = click.types.IntRange(min=min_val, max=max_val, min_open=True, clamp=True)
    range_max_open = click.types.IntRange(min=min_val, max=max_val, max_open=True, clamp=True)
    
    result_min_open = range_min_open.convert(value, None, None)
    result_max_open = range_max_open.convert(value, None, None)
    
    if value <= min_val:
        assert result_min_open == min_val + 1
    else:
        assert result_min_open <= max_val
    
    if value >= max_val:
        assert result_max_open == max_val - 1
    else:
        assert result_max_open >= min_val


@given(st.lists(st.dates().map(lambda d: d.strftime("%Y-%m-%d"))))
def test_datetime_format_parsing(date_strings):
    """Test DateTime type parsing with various formats"""
    assume(len(date_strings) > 0)
    
    dt_type = click.types.DateTime(formats=["%Y-%m-%d"])
    
    for date_str in date_strings:
        result = dt_type.convert(date_str, None, None)
        assert isinstance(result, datetime)
        assert result.strftime("%Y-%m-%d") == date_str


@given(st.text())
def test_bool_type_parsing(value):
    """Test bool type parsing various string representations"""
    bool_type = click.types.BoolParamType()
    
    if value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}:
        result = bool_type.convert(value, None, None)
        assert result is True
    elif value.strip().lower() in {"0", "false", "f", "no", "n", "off"}:
        result = bool_type.convert(value, None, None)
        assert result is False
    else:
        try:
            bool_type.convert(value, None, None)
        except click.types.BadParameter:
            pass


@given(st.text())
def test_split_envvar_value_property(value):
    """Test envvar splitting behavior"""
    param_type = click.types.ParamType()
    
    result = param_type.split_envvar_value(value)
    
    assert isinstance(result, list)
    
    if param_type.envvar_list_splitter is None:
        if value:
            assert all(item for item in result)
    else:
        joined = param_type.envvar_list_splitter.join(result)
        if value:
            assert value == joined


@given(st.lists(st.integers()))
def test_tuple_type_conversion(values):
    """Test Tuple type conversion with multiple types"""
    assume(1 <= len(values) <= 5)
    
    types = [click.types.IntParamType() for _ in values]
    tuple_type = click.types.Tuple(types)
    
    result = tuple_type.convert(values, None, None)
    
    assert isinstance(result, tuple)
    assert len(result) == len(values)
    assert all(isinstance(v, int) for v in result)
    assert list(result) == values