import math
import uuid as uuid_module
from datetime import datetime
from hypothesis import assume, given, strategies as st, settings, HealthCheck
import click.types


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-1e9, max_value=1e9))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_float_range_clamp_property(min_val, max_val, test_val):
    """Test that float clamping always produces values within bounds"""
    assume(min_val < max_val)
    assume(abs(max_val - min_val) < 1e6)
    assume(abs(max_val - min_val) > 1e-10)
    
    float_range = click.types.FloatRange(min=min_val, max=max_val, clamp=True)
    result = float_range.convert(test_val, None, None)
    
    assert min_val <= result <= max_val
    
    if test_val < min_val:
        assert math.isclose(result, min_val, rel_tol=1e-9)
    elif test_val > max_val:
        assert math.isclose(result, max_val, rel_tol=1e-9)
    else:
        assert math.isclose(result, test_val, rel_tol=1e-9)


@given(st.text())
def test_datetime_format_year_padding(date_str):
    """Test DateTime type parsing with year padding issues"""
    dt_type = click.types.DateTime(formats=["%Y-%m-%d"])
    
    if "-" in date_str:
        parts = date_str.split("-")
        if len(parts) == 3:
            try:
                year_str, month_str, day_str = parts
                year = int(year_str)
                month = int(month_str)
                day = int(day_str)
                
                if 1 <= year <= 999 and 1 <= month <= 12 and 1 <= day <= 31:
                    try:
                        result = dt_type.convert(date_str, None, None)
                        assert False, f"Should have failed for 3-digit year: {date_str}"
                    except click.types.BadParameter:
                        pass
            except (ValueError, IndexError):
                pass


@given(st.lists(st.text(min_size=1)))
def test_choice_duplicate_normalization_bug(choices):
    """Test Choice type with values that normalize to the same string"""
    assume(len(choices) >= 2)
    
    choices_with_dup = list(choices)
    if len(choices) >= 2:
        choices_with_dup[0] = "TEST"
        choices_with_dup[1] = "test"
    
    choice_type = click.types.Choice(choices_with_dup, case_sensitive=False)
    normalized = choice_type._normalized_mapping(ctx=None)
    
    converted_upper = choice_type.convert("TEST", None, None)
    converted_lower = choice_type.convert("test", None, None)
    
    assert converted_upper in choices_with_dup
    assert converted_lower in choices_with_dup


@given(st.text())
def test_split_envvar_empty_items(value):
    """Test envvar splitting with empty items"""
    param_type = click.types.ParamType()
    param_type.envvar_list_splitter = ":"
    
    result = param_type.split_envvar_value(value)
    
    if value == "":
        assert result == [""]
    elif ":" in value:
        expected = value.split(":")
        assert result == expected
        
        if value.startswith(":"):
            assert result[0] == ""
        if value.endswith(":"):
            assert result[-1] == ""


@given(st.integers(), st.integers())
def test_int_range_describe_range(min_val, max_val):
    """Test range description formatting"""
    if min_val == max_val:
        return
        
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    
    int_range = click.types.IntRange(min=min_val, max=max_val)
    description = int_range._describe_range()
    
    assert str(min_val) in description
    assert str(max_val) in description
    assert "x" in description


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
def test_float_range_open_clamp_error(value):
    """Test that FloatRange with open bounds and clamp raises error at init"""
    try:
        float_range = click.types.FloatRange(min=0.0, max=10.0, min_open=True, clamp=True)
        assert False, "Should have raised TypeError for open bounds with clamp"
    except TypeError as e:
        assert "Clamping is not supported for open bounds" in str(e)


@given(st.text())
def test_unprocessed_param_type_bypass(value):
    """Test that UnprocessedParamType bypasses conversion"""
    unprocessed = click.types.UnprocessedParamType()
    
    result = unprocessed.convert(value, None, None)
    assert result is value
    
    bytes_value = b"test"
    result = unprocessed.convert(bytes_value, None, None)
    assert result is bytes_value


@given(st.sampled_from([True, False, 1, 0, "true", "false"]))
def test_bool_edge_cases(value):
    """Test bool type with edge cases"""
    bool_type = click.types.BoolParamType()
    
    result = bool_type.convert(value, None, None)
    
    if value in {True, 1, "true"}:
        assert result is True
    elif value in {False, 0, "false"}:
        assert result is False


@given(st.integers(min_value=-100, max_value=100))
def test_int_range_boundary_comparison_operators(value):
    """Test boundary comparison operators in IntRange"""
    min_val = 0
    max_val = 10
    
    range_closed = click.types.IntRange(min=min_val, max=max_val)
    range_min_open = click.types.IntRange(min=min_val, max=max_val, min_open=True) 
    range_max_open = click.types.IntRange(min=min_val, max=max_val, max_open=True)
    range_both_open = click.types.IntRange(min=min_val, max=max_val, min_open=True, max_open=True)
    
    if value == min_val:
        result = range_closed.convert(value, None, None)
        assert result == min_val
        
        try:
            range_min_open.convert(value, None, None)
            assert False, "Min boundary should fail with min_open"
        except click.types.BadParameter:
            pass
            
        try:
            range_both_open.convert(value, None, None)
            assert False, "Min boundary should fail with both open"
        except click.types.BadParameter:
            pass
    
    if value == max_val:
        result = range_closed.convert(value, None, None)
        assert result == max_val
        
        try:
            range_max_open.convert(value, None, None)
            assert False, "Max boundary should fail with max_open"
        except click.types.BadParameter:
            pass
            
        try:
            range_both_open.convert(value, None, None)
            assert False, "Max boundary should fail with both open"
        except click.types.BadParameter:
            pass