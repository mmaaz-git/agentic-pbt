import math
import re
from hypothesis import assume, given, settings, strategies as st
from tqdm.std import Bar, EMA, tqdm
from tqdm.utils import disp_len, disp_trim

# Test Bar class properties
@given(
    frac=st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False),
    default_len=st.integers(min_value=1, max_value=100)
)
def test_bar_fraction_clamping(frac, default_len):
    """Test that Bar fractions are properly clamped to [0, 1]"""
    bar = Bar(frac, default_len=default_len)
    assert 0 <= bar.frac <= 1, f"Bar fraction {bar.frac} not in [0, 1]"

@given(
    frac=st.floats(min_value=0, max_value=1, allow_nan=False),
    default_len=st.integers(min_value=1, max_value=50),
    format_spec=st.text(min_size=0, max_size=3).filter(lambda x: x.replace('-', '').replace('a', '').replace('u', '').replace('b', '').isdigit() or x == '')
)
def test_bar_output_length(frac, default_len, format_spec):
    """Test that Bar output has the expected display length"""
    bar = Bar(frac, default_len=default_len)
    output = format(bar, format_spec)
    
    # Remove ANSI color codes if present
    ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
    clean_output = ansi_pattern.sub('', output)
    
    # Expected length calculation
    if format_spec:
        if format_spec[-1:].lower() in 'aub':
            spec_without_type = format_spec[:-1]
            if spec_without_type:
                n_bars = int(spec_without_type)
                expected_len = n_bars + default_len if n_bars < 0 else n_bars
            else:
                expected_len = default_len
        else:
            if format_spec.lstrip('-').isdigit():
                n_bars = int(format_spec)
                expected_len = n_bars + default_len if n_bars < 0 else n_bars
            else:
                expected_len = default_len
    else:
        expected_len = default_len
    
    # Handle edge cases
    if expected_len <= 0:
        expected_len = default_len
    
    assert len(clean_output) == expected_len, f"Bar output length {len(clean_output)} != expected {expected_len}"

# Test EMA class properties
@given(
    smoothing=st.floats(min_value=0, max_value=1, allow_nan=False),
    values=st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False), min_size=1, max_size=100)
)
def test_ema_bounds(smoothing, values):
    """Test that EMA output is bounded by input values"""
    ema = EMA(smoothing=smoothing)
    
    for val in values:
        result = ema(val)
    
    # EMA should be bounded by min and max of all values seen
    min_val = min(values)
    max_val = max(values)
    
    # With some tolerance for floating point arithmetic
    assert min_val - 1e-10 <= result <= max_val + 1e-10, f"EMA result {result} not in range [{min_val}, {max_val}]"

@given(
    smoothing=st.floats(min_value=0.001, max_value=0.999, allow_nan=False),
    value=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
)
def test_ema_single_value_convergence(smoothing, value):
    """Test that EMA converges to a constant value when fed the same input"""
    ema = EMA(smoothing=smoothing)
    
    # Feed the same value multiple times
    for _ in range(100):
        result = ema(value)
    
    # After many iterations, EMA should converge very close to the input value
    assert math.isclose(result, value, rel_tol=1e-6), f"EMA did not converge to {value}, got {result}"

# Test format_sizeof properties
@given(
    num=st.floats(min_value=1, max_value=1e30, allow_nan=False, allow_infinity=False),
    divisor=st.integers(min_value=1000, max_value=1024)
)
def test_format_sizeof_monotonic(num, divisor):
    """Test that format_sizeof preserves order for positive numbers"""
    from tqdm.std import tqdm
    
    num2 = num * 2
    
    formatted1 = tqdm.format_sizeof(num, divisor=divisor)
    formatted2 = tqdm.format_sizeof(num2, divisor=divisor)
    
    # Extract numeric value and unit from formatted strings
    def extract_value(s):
        match = re.match(r'([\d.]+)([kMGTPEZY]?)', s)
        if match:
            val, unit = match.groups()
            multipliers = {'': 1, 'k': divisor, 'M': divisor**2, 'G': divisor**3,
                          'T': divisor**4, 'P': divisor**5, 'E': divisor**6,
                          'Z': divisor**7, 'Y': divisor**8}
            return float(val) * multipliers.get(unit, divisor**9)
        return 0
    
    val1 = extract_value(formatted1)
    val2 = extract_value(formatted2)
    
    # Since num2 > num, the extracted value should also maintain that relationship
    # Allow for small rounding differences
    assert val1 <= val2 * 1.001, f"format_sizeof not monotonic: {num} -> {formatted1} ({val1}), {num2} -> {formatted2} ({val2})"

# Test format_interval properties
@given(seconds=st.integers(min_value=0, max_value=3600*24*7))  # Up to a week
def test_format_interval_parseable(seconds):
    """Test that format_interval output can be parsed back"""
    from tqdm.std import tqdm
    
    formatted = tqdm.format_interval(seconds)
    
    # Parse the formatted time back
    parts = formatted.split(':')
    if len(parts) == 2:  # MM:SS
        parsed_seconds = int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:  # H:MM:SS
        parsed_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    else:
        parsed_seconds = -1
    
    assert parsed_seconds == seconds, f"format_interval round-trip failed: {seconds} -> {formatted} -> {parsed_seconds}"

# Test disp_len and disp_trim properties
@given(
    text=st.text(min_size=0, max_size=100),
    ansi_codes=st.lists(
        st.sampled_from(['\x1b[0m', '\x1b[31m', '\x1b[1m', '\x1b[32m', '\x1b[33m']),
        min_size=0,
        max_size=5
    )
)
def test_disp_len_ansi_invariant(text, ansi_codes):
    """Test that ANSI codes don't affect display length"""
    # Create text with ANSI codes inserted
    text_with_ansi = text
    for code in ansi_codes:
        # Insert ANSI code at a random position
        if text_with_ansi:
            pos = len(text_with_ansi) // 2
            text_with_ansi = text_with_ansi[:pos] + code + text_with_ansi[pos:]
    
    plain_len = disp_len(text)
    ansi_len = disp_len(text_with_ansi)
    
    assert plain_len == ansi_len, f"ANSI codes affected display length: plain={plain_len}, with_ansi={ansi_len}"

@given(
    text=st.text(min_size=0, max_size=100),
    trim_length=st.integers(min_value=0, max_value=50)
)
def test_disp_trim_length_property(text, trim_length):
    """Test that disp_trim produces output with correct display length"""
    # Skip strings with wide characters for this test
    assume(all(ord(c) < 0x3000 for c in text))  # Skip CJK and other wide chars
    
    trimmed = disp_trim(text, trim_length)
    trimmed_len = disp_len(trimmed)
    
    # The trimmed display length should be at most the requested length
    assert trimmed_len <= trim_length, f"disp_trim produced too long output: {trimmed_len} > {trim_length}"
    
    # If original was shorter, it should remain unchanged
    if disp_len(text) <= trim_length:
        # Remove potential ANSI reset code for comparison
        trimmed_clean = trimmed.replace('\x1b[0m', '')
        assert trimmed_clean == text, f"disp_trim modified short text unnecessarily"

@given(
    text=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    ansi_codes=st.lists(
        st.sampled_from(['\x1b[31m', '\x1b[32m', '\x1b[1m']),
        min_size=1,
        max_size=3
    ),
    trim_length=st.integers(min_value=1, max_value=50)
)
def test_disp_trim_ansi_reset(text, ansi_codes, trim_length):
    """Test that disp_trim adds ANSI reset when needed"""
    # Create text with ANSI codes
    text_with_ansi = ansi_codes[0] + text
    for code in ansi_codes[1:]:
        pos = len(text_with_ansi) // 2
        text_with_ansi = text_with_ansi[:pos] + code + text_with_ansi[pos:]
    
    trimmed = disp_trim(text_with_ansi, trim_length)
    
    # If ANSI codes were present and text was trimmed, should end with reset
    if '\x1b[' in text_with_ansi and disp_len(text_with_ansi) > trim_length:
        if '\x1b[' in trimmed:  # If ANSI codes remain after trimming
            assert trimmed.endswith('\x1b[0m'), f"disp_trim didn't add ANSI reset code"

# Test format_num properties
@given(
    n=st.one_of(
        st.integers(min_value=-1e15, max_value=1e15),
        st.floats(min_value=-1e15, max_value=1e15, allow_nan=False, allow_infinity=False)
    )
)
def test_format_num_parseable(n):
    """Test that format_num output can be parsed back to a number"""
    from tqdm.std import tqdm
    
    formatted = tqdm.format_num(n)
    
    # Should be able to parse the formatted number back
    try:
        parsed = float(formatted)
        # Allow for some loss of precision in scientific notation
        if 'e' in formatted.lower():
            assert math.isclose(parsed, float(n), rel_tol=1e-2), f"format_num roundtrip failed: {n} -> {formatted} -> {parsed}"
        else:
            assert math.isclose(parsed, float(n), rel_tol=1e-10), f"format_num roundtrip failed: {n} -> {formatted} -> {parsed}"
    except ValueError:
        assert False, f"format_num produced unparseable output: {formatted}"