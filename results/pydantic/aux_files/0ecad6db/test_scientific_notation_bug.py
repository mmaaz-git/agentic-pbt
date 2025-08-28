import math
from hypothesis import given, strategies as st, settings
from pydantic.color import parse_str, Color


# Test that reveals the scientific notation bug
@given(
    st.floats(min_value=0, max_value=360, allow_nan=False),
    st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=1000)
def test_hsl_string_format_bug(h, s, l):
    # When Python formats very small floats, it uses scientific notation
    hsl_str = f"hsl({h}, {s}%, {l}%)"
    
    # This should always work according to the API
    result = parse_str(hsl_str)
    
    # All RGB values should be in [0, 1]
    assert 0 <= result.r <= 1
    assert 0 <= result.g <= 1
    assert 0 <= result.b <= 1


# Test RGB format with scientific notation
@given(
    st.floats(min_value=0, max_value=255, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0, max_value=255, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0, max_value=255, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=1000)
def test_rgb_string_format_bug(r, g, b):
    rgb_str = f"rgb({r}, {g}, {b})"
    
    # This should always work
    result = parse_str(rgb_str)
    
    # Check values are normalized to [0, 1]
    assert 0 <= result.r <= 1
    assert 0 <= result.g <= 1
    assert 0 <= result.b <= 1


if __name__ == "__main__":
    # Minimal reproduction
    print("Minimal reproduction of the bug:")
    
    # These values trigger scientific notation in Python's default formatting
    test_cases = [
        ("HSL with tiny lightness", "hsl(0, 0%, 5.3023639748142e-39%)"),
        ("HSL with tiny saturation", "hsl(0, 1e-40%, 50%)"),
        ("RGB with tiny value", "rgb(1e-40, 0, 0)"),
        ("RGBA with scientific alpha", "rgba(255, 255, 255, 1e-10)"),
    ]
    
    for desc, color_str in test_cases:
        try:
            result = parse_str(color_str)
            print(f"✓ {desc}: {color_str} -> Success")
        except Exception as e:
            print(f"✗ {desc}: {color_str} -> FAILED")
            print(f"  Error: {e}")