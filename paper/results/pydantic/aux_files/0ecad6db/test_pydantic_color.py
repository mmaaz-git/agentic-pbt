import math
from hypothesis import given, strategies as st, assume, settings
import pydantic.color
from pydantic.color import (
    float_to_255, parse_color_value, parse_str, parse_tuple,
    ints_to_rgba, parse_float_alpha, parse_hsl,
    RGBA, Color, COLORS_BY_NAME
)


# Test 1: float_to_255 invariant - result must be in [0, 255]
@given(st.floats(min_value=0, max_value=1, allow_nan=False))
def test_float_to_255_invariant(value):
    result = float_to_255(value)
    assert isinstance(result, int)
    assert 0 <= result <= 255


# Test 2: parse_color_value invariant - returns value in [0, 1]
@given(st.floats(min_value=0, max_value=255, allow_nan=False))
def test_parse_color_value_float_invariant(value):
    result = parse_color_value(value, max_val=255)
    assert 0 <= result <= 1


@given(st.integers(min_value=0, max_value=255))
def test_parse_color_value_int_invariant(value):
    result = parse_color_value(value, max_val=255)
    assert 0 <= result <= 1


# Test 3: Hex format confluence - different prefixes parse to same RGBA
@given(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)
def test_hex_format_confluence(r, g, b):
    hex_value = f"{r:02x}{g:02x}{b:02x}"
    
    # Different valid hex representations
    result1 = parse_str(f"#{hex_value}")
    result2 = parse_str(f"0x{hex_value}")
    result3 = parse_str(hex_value)
    
    # All should parse to same RGBA values
    assert math.isclose(result1.r, result2.r, abs_tol=1e-9)
    assert math.isclose(result1.g, result2.g, abs_tol=1e-9)
    assert math.isclose(result1.b, result2.b, abs_tol=1e-9)
    assert math.isclose(result2.r, result3.r, abs_tol=1e-9)
    assert math.isclose(result2.g, result3.g, abs_tol=1e-9)
    assert math.isclose(result2.b, result3.b, abs_tol=1e-9)


# Test 4: RGB string parsing - values should be normalized correctly
@given(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)
def test_rgb_string_parsing(r, g, b):
    rgb_str = f"rgb({r}, {g}, {b})"
    result = parse_str(rgb_str)
    
    # Check values are normalized to [0, 1]
    assert 0 <= result.r <= 1
    assert 0 <= result.g <= 1
    assert 0 <= result.b <= 1
    
    # Check reverse conversion is approximately correct
    assert abs(float_to_255(result.r) - r) <= 1
    assert abs(float_to_255(result.g) - g) <= 1
    assert abs(float_to_255(result.b) - b) <= 1


# Test 5: Named colors consistency
@given(st.sampled_from(list(COLORS_BY_NAME.keys())))
def test_named_colors_parsing(color_name):
    expected_rgb = COLORS_BY_NAME[color_name]
    
    # Parse the color name
    result = parse_str(color_name)
    
    # Convert back to RGB tuple
    r_int = float_to_255(result.r)
    g_int = float_to_255(result.g)
    b_int = float_to_255(result.b)
    
    # Should match expected values
    assert r_int == expected_rgb[0]
    assert g_int == expected_rgb[1]
    assert b_int == expected_rgb[2]


# Test 6: Tuple parsing invariant
@given(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)
def test_tuple_parsing_3_values(r, g, b):
    result = parse_tuple((r, g, b))
    
    # Check all values are in [0, 1]
    assert 0 <= result.r <= 1
    assert 0 <= result.g <= 1
    assert 0 <= result.b <= 1
    assert result.alpha is None


# Test 7: Alpha parsing - should be in [0, 1] or None
@given(st.floats(min_value=0, max_value=1, allow_nan=False))
def test_parse_float_alpha_invariant(value):
    result = parse_float_alpha(value)
    
    if math.isclose(value, 1):
        assert result is None
    else:
        assert result is not None
        assert 0 <= result <= 1


# Test 8: RGBA string with alpha
@given(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.floats(min_value=0, max_value=0.99, allow_nan=False)
)
def test_rgba_string_with_alpha(r, g, b, alpha):
    rgba_str = f"rgba({r}, {g}, {b}, {alpha:.2f})"
    result = parse_str(rgba_str)
    
    # Check RGB values
    assert 0 <= result.r <= 1
    assert 0 <= result.g <= 1
    assert 0 <= result.b <= 1
    
    # Check alpha
    if result.alpha is not None:
        assert 0 <= result.alpha <= 1


# Test 9: Case insensitivity for named colors
@given(st.sampled_from(list(COLORS_BY_NAME.keys())))
def test_named_colors_case_insensitive(color_name):
    result_lower = parse_str(color_name.lower())
    result_upper = parse_str(color_name.upper())
    result_mixed = parse_str(color_name.title())
    
    # All should give same result
    assert math.isclose(result_lower.r, result_upper.r, abs_tol=1e-9)
    assert math.isclose(result_lower.g, result_upper.g, abs_tol=1e-9)
    assert math.isclose(result_lower.b, result_upper.b, abs_tol=1e-9)
    assert math.isclose(result_upper.r, result_mixed.r, abs_tol=1e-9)
    assert math.isclose(result_upper.g, result_mixed.g, abs_tol=1e-9)
    assert math.isclose(result_upper.b, result_mixed.b, abs_tol=1e-9)


# Test 10: float_to_255 edge cases
@given(st.floats(min_value=0, max_value=1, allow_nan=False))
def test_float_to_255_round_trip_property(value):
    # Convert to int and back
    int_val = float_to_255(value)
    
    # The conversion should preserve approximate value
    # Due to rounding, we need tolerance
    back_value = int_val / 255.0
    assert abs(back_value - value) <= 1/255.0


# Test 11: Hex short format parsing
@given(
    st.integers(min_value=0, max_value=15),
    st.integers(min_value=0, max_value=15),
    st.integers(min_value=0, max_value=15)
)
def test_hex_short_format(r, g, b):
    hex_short = f"#{r:x}{g:x}{b:x}"
    result = parse_str(hex_short)
    
    # Short hex is doubled (e.g., #abc -> #aabbcc)
    expected_r = (r * 17) / 255.0  # r * 17 = r * 0x11
    expected_g = (g * 17) / 255.0
    expected_b = (b * 17) / 255.0
    
    assert math.isclose(result.r, expected_r, abs_tol=1/255.0)
    assert math.isclose(result.g, expected_g, abs_tol=1/255.0)
    assert math.isclose(result.b, expected_b, abs_tol=1/255.0)


# Test 12: Color class initialization and methods
@given(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)
def test_color_class_rgb_tuple(r, g, b):
    color = Color((r, g, b))
    
    # Get RGB tuple back
    rgb_tuple = color.as_rgb_tuple()
    
    assert rgb_tuple[0] == float_to_255(color._rgba.r)
    assert rgb_tuple[1] == float_to_255(color._rgba.g)
    assert rgb_tuple[2] == float_to_255(color._rgba.b)


# Test 13: HSL parsing with different angle units
@given(
    st.floats(min_value=0, max_value=360, allow_nan=False),
    st.floats(min_value=0, max_value=100, allow_nan=False),
    st.floats(min_value=0, max_value=100, allow_nan=False)
)
def test_hsl_parsing_degrees(h, s, l):
    hsl_str = f"hsl({h}, {s}%, {l}%)"
    result = parse_str(hsl_str)
    
    # All RGB values should be in [0, 1]
    assert 0 <= result.r <= 1
    assert 0 <= result.g <= 1
    assert 0 <= result.b <= 1