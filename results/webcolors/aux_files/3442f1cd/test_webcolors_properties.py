"""Property-based tests for webcolors module using Hypothesis."""

import math
import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/webcolors_env/lib/python3.13/site-packages')

import webcolors
from hypothesis import assume, given, strategies as st, settings


# Strategy for valid hex colors - both 3 and 6 digit formats
hex_digit = st.sampled_from("0123456789abcdefABCDEF")
hex_color_3 = st.builds(
    lambda d1, d2, d3: f"#{d1}{d2}{d3}",
    hex_digit, hex_digit, hex_digit
)
hex_color_6 = st.builds(
    lambda d1, d2, d3, d4, d5, d6: f"#{d1}{d2}{d3}{d4}{d5}{d6}",
    hex_digit, hex_digit, hex_digit, hex_digit, hex_digit, hex_digit
)
valid_hex_colors = st.one_of(hex_color_3, hex_color_6)


# Strategy for RGB integer triplets (allowing out-of-bounds for testing clamping)
rgb_integers = st.tuples(
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-1000, max_value=1000)
)

# Strategy for valid RGB integers (0-255)
valid_rgb_integers = st.tuples(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)

# Strategy for RGB percent triplets  
def percent_string(value):
    """Generate a percent string from a float value."""
    if value == int(value):
        return f"{int(value)}%"
    return f"{value}%"

rgb_percents = st.tuples(
    st.floats(min_value=-200, max_value=200, allow_nan=False).map(percent_string),
    st.floats(min_value=-200, max_value=200, allow_nan=False).map(percent_string),
    st.floats(min_value=-200, max_value=200, allow_nan=False).map(percent_string)
)

# Valid percent values (0-100%)
valid_rgb_percents = st.tuples(
    st.floats(min_value=0, max_value=100, allow_nan=False).map(percent_string),
    st.floats(min_value=0, max_value=100, allow_nan=False).map(percent_string),
    st.floats(min_value=0, max_value=100, allow_nan=False).map(percent_string)
)


@given(valid_hex_colors)
def test_hex_normalization_idempotence(hex_value):
    """Test that normalizing a hex value twice gives the same result."""
    normalized_once = webcolors.normalize_hex(hex_value)
    normalized_twice = webcolors.normalize_hex(normalized_once)
    assert normalized_once == normalized_twice
    # Also verify format: # followed by 6 lowercase hex digits
    assert re.match(r'^#[0-9a-f]{6}$', normalized_once)


@given(valid_rgb_integers)
def test_rgb_to_hex_to_rgb_round_trip(rgb):
    """Test that converting RGB to hex and back preserves values."""
    hex_value = webcolors.rgb_to_hex(rgb)
    rgb_back = webcolors.hex_to_rgb(hex_value)
    # Should be exactly equal since we're using valid values
    assert rgb_back == webcolors.IntegerRGB(*rgb)


@given(rgb_integers)
def test_integer_rgb_normalization_clamping(rgb):
    """Test that RGB integer normalization clamps values to 0-255."""
    normalized = webcolors.normalize_integer_triplet(rgb)
    for value in normalized:
        assert 0 <= value <= 255
    # Verify clamping behavior
    expected = webcolors.IntegerRGB(
        max(0, min(255, rgb[0])),
        max(0, min(255, rgb[1])),
        max(0, min(255, rgb[2]))
    )
    assert normalized == expected


@given(rgb_percents)
def test_percent_rgb_normalization_clamping(rgb_percent):
    """Test that RGB percent normalization clamps values to 0%-100%."""
    normalized = webcolors.normalize_percent_triplet(rgb_percent)
    for value in normalized:
        # Extract numeric value from percentage string
        numeric = float(value.rstrip('%'))
        assert 0 <= numeric <= 100


@given(valid_rgb_percents)
def test_percent_to_integer_to_percent_precision(rgb_percent):
    """Test precision in percent to integer to percent conversion."""
    # Convert percent to integer and back
    integer_rgb = webcolors.rgb_percent_to_rgb(rgb_percent)
    percent_back = webcolors.rgb_to_rgb_percent(integer_rgb)
    
    # Check if we get unexpected precision loss
    # The code mentions special cases for certain values
    for orig, back in zip(rgb_percent, percent_back):
        orig_val = float(orig.rstrip('%'))
        back_val = float(back.rstrip('%'))
        
        # Special values that should be preserved exactly according to the code
        special_mappings = {
            100.0: 255,
            50.0: 128,
            25.0: 64,
            12.5: 32,
            6.25: 16,
            0.0: 0
        }
        
        if orig_val in special_mappings:
            # These should round-trip exactly
            assert math.isclose(orig_val, back_val, abs_tol=0.01), \
                f"Special value {orig_val}% didn't round-trip correctly: got {back_val}%"


# Test HTML5 simple color format validation
@given(st.text())
def test_html5_simple_color_format_validation(text):
    """Test that HTML5 simple color parsing enforces format constraints."""
    try:
        result = webcolors.html5_parse_simple_color(text)
        # If it succeeds, verify the input matched the required format
        assert len(text) == 7
        assert text[0] == '#'
        assert all(c in '0123456789abcdefABCDEF' for c in text[1:])
    except ValueError:
        # Should fail if format is invalid
        is_valid_format = (
            len(text) == 7 and
            text[0] == '#' and
            all(c in '0123456789abcdefABCDEF' for c in text[1:])
        )
        assert not is_valid_format


# Test named color conversions with actual color names
named_colors = st.sampled_from([
    "red", "green", "blue", "white", "black", "yellow", "cyan", "magenta",
    "navy", "olive", "purple", "teal", "silver", "gray", "maroon", "lime",
    "aqua", "fuchsia", "orange"  # orange is CSS2.1+
])

@given(named_colors)
def test_name_to_hex_to_name_consistency(name):
    """Test that converting a name to hex gives expected results."""
    try:
        hex_value = webcolors.name_to_hex(name)
        # Should be a valid hex color
        assert re.match(r'^#[0-9a-f]{6}$', hex_value)
        
        # Try to convert back - might not always work due to aliasing
        try:
            name_back = webcolors.hex_to_name(hex_value)
            # If it works, the name should be valid
            assert name_back.lower() in ["gray", "grey", "lightgray", "lightgrey", 
                                         "darkgray", "darkgrey", "dimgray", "dimgrey",
                                         "slategray", "slategrey", "darkslategray", 
                                         "darkslategrey"] or name_back == name
        except ValueError:
            # Some hex values might not have a name
            pass
    except ValueError:
        # Some names might not be in all specs
        pass


# Test hex to RGB to hex round-trip with various hex formats
@given(valid_hex_colors)
def test_hex_to_rgb_to_hex_round_trip(hex_value):
    """Test that converting hex to RGB and back preserves the normalized value."""
    normalized_hex = webcolors.normalize_hex(hex_value)
    rgb = webcolors.hex_to_rgb(hex_value)
    hex_back = webcolors.rgb_to_hex(rgb)
    assert hex_back == normalized_hex


# Test edge cases for percent to integer conversion
special_percents = st.sampled_from(["0%", "6.25%", "12.5%", "25%", "50%", "100%"])

@given(st.tuples(special_percents, special_percents, special_percents))
def test_special_percent_values_preservation(rgb_percent):
    """Test that special percentage values are preserved correctly."""
    integer_rgb = webcolors.rgb_percent_to_rgb(rgb_percent)
    percent_back = webcolors.rgb_to_rgb_percent(integer_rgb)
    
    # These special values should round-trip exactly
    assert rgb_percent == percent_back