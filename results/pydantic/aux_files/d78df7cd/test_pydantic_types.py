"""Property-based tests for pydantic.types"""

import math
import sys
from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings
from pydantic import BaseModel, ValidationError
from pydantic.types import ByteSize, SecretStr, SecretBytes, ImportString
import pytest


# ByteSize Tests

@given(st.integers(min_value=0, max_value=10**15))  # Reasonable byte range
def test_bytesize_integer_initialization(value):
    """ByteSize should accept plain integers and preserve their value"""
    class Model(BaseModel):
        size: ByteSize
    
    m = Model(size=value)
    assert int(m.size) == value
    assert m.size.to("B") == float(value)


@given(st.integers(min_value=1, max_value=10**12))  # Up to TB range
def test_bytesize_string_with_B_suffix(value):
    """ByteSize should parse strings with 'B' suffix correctly"""
    class Model(BaseModel):
        size: ByteSize
    
    m = Model(size=f"{value}B")
    assert int(m.size) == value


@given(
    st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
    st.sampled_from(["KB", "MB", "GB", "KiB", "MiB", "GiB"])
)
def test_bytesize_unit_conversion_round_trip(value, unit):
    """Converting ByteSize to a unit and back should preserve value within floating point precision"""
    class Model(BaseModel):
        size: ByteSize
    
    # Create ByteSize from string with unit
    m = Model(size=f"{value}{unit}")
    bs = m.size
    
    # Convert to that unit and check it matches (within floating point precision)
    converted = bs.to(unit)
    assert math.isclose(converted, value, rel_tol=1e-9)


@given(st.integers(min_value=0, max_value=10**15))
def test_bytesize_to_bytes_invariant(value):
    """ByteSize.to('B') should always equal the integer value"""
    class Model(BaseModel):
        size: ByteSize
    
    m = Model(size=value)
    assert m.size.to("B") == float(value)


@given(st.integers(min_value=1, max_value=10**12))
def test_bytesize_human_readable_parseable(value):
    """human_readable() output should be parseable back to ByteSize"""
    class Model(BaseModel):
        size: ByteSize
    
    m1 = Model(size=value)
    human = m1.size.human_readable()
    
    # human_readable might return values like "1.0KiB"
    # Try to parse it back
    try:
        m2 = Model(size=human)
        # The values might not be exactly equal due to rounding in human_readable
        # but they should be close
        ratio = int(m2.size) / value
        assert 0.99 <= ratio <= 1.01, f"Mismatch: {value} -> {human} -> {int(m2.size)}"
    except ValidationError:
        # If human_readable produces unparseable output, that's a bug
        pytest.fail(f"human_readable produced unparseable output: {human}")


# SecretStr Tests

@given(st.text(min_size=1))
def test_secretstr_never_reveals_in_str(secret):
    """SecretStr should never reveal the secret in str()"""
    s = SecretStr(secret)
    str_repr = str(s)
    assert secret not in str_repr
    assert str_repr == "**********"


@given(st.text(min_size=1))
def test_secretstr_never_reveals_in_repr(secret):
    """SecretStr should never reveal the secret in repr()"""
    s = SecretStr(secret)
    repr_str = repr(s)
    assert secret not in repr_str
    assert "**********" in repr_str


@given(st.text(min_size=1))
def test_secretstr_get_secret_value_returns_original(secret):
    """get_secret_value() should return the original secret"""
    s = SecretStr(secret)
    assert s.get_secret_value() == secret


# SecretBytes Tests

@given(st.binary(min_size=1))
def test_secretbytes_never_reveals_in_str(secret):
    """SecretBytes should never reveal the secret in str()"""
    s = SecretBytes(secret)
    str_repr = str(s)
    assert secret not in str_repr.encode()
    assert str_repr == "b'**********'"


@given(st.binary(min_size=1))
def test_secretbytes_never_reveals_in_repr(secret):
    """SecretBytes should never reveal the secret in repr()"""
    s = SecretBytes(secret)
    repr_str = repr(s)
    assert secret not in repr_str.encode()
    assert "b'**********'" in repr_str


@given(st.binary(min_size=1))
def test_secretbytes_get_secret_value_returns_original(secret):
    """get_secret_value() should return the original secret"""
    s = SecretBytes(secret)
    assert s.get_secret_value() == secret


# ImportString Tests

@given(st.sampled_from([
    "math.pi",
    "math.e", 
    "sys.maxsize",
    "sys.version",
]))
def test_importstring_imports_constants_correctly(import_path):
    """ImportString should import constants that match direct import"""
    class Model(BaseModel):
        obj: ImportString
    
    m = Model(obj=import_path)
    imported = m.obj
    
    # Compare with direct import
    module_name, attr_name = import_path.rsplit(".", 1)
    if module_name == "math":
        import math
        expected = getattr(math, attr_name)
    elif module_name == "sys":
        import sys
        expected = getattr(sys, attr_name)
    
    assert imported == expected


@given(st.sampled_from([
    "math.ceil",
    "math.floor",
    "math.sqrt",
    "math.isnan",
    "math.isinf",
]))
def test_importstring_imports_functions_correctly(import_path):
    """ImportString should import functions that work identically to direct import"""
    class Model(BaseModel):
        obj: ImportString
    
    m = Model(obj=import_path)
    imported_func = m.obj
    
    # Compare with direct import
    import math
    _, func_name = import_path.rsplit(".", 1)
    expected_func = getattr(math, func_name)
    
    # Test that they're the same function
    assert imported_func is expected_func
    
    # Test with some values
    if func_name in ["ceil", "floor", "sqrt"]:
        test_val = 4.5 if func_name != "sqrt" else 4.0
        assert imported_func(test_val) == expected_func(test_val)


# Edge case tests for ByteSize

@given(st.floats(min_value=0.001, max_value=999.999, allow_nan=False, allow_infinity=False))
def test_bytesize_decimal_kb_conversion(value):
    """ByteSize should handle decimal KB values correctly"""
    class Model(BaseModel):
        size: ByteSize
    
    m = Model(size=f"{value}KB")
    expected_bytes = int(value * 1000)  # KB is 1000 bytes
    actual_bytes = int(m.size)
    
    # Allow for small rounding differences
    assert abs(actual_bytes - expected_bytes) <= 1


@given(st.floats(min_value=0.001, max_value=999.999, allow_nan=False, allow_infinity=False))
def test_bytesize_decimal_kib_conversion(value):
    """ByteSize should handle decimal KiB values correctly"""
    class Model(BaseModel):
        size: ByteSize
    
    m = Model(size=f"{value}KiB")
    expected_bytes = int(value * 1024)  # KiB is 1024 bytes
    actual_bytes = int(m.size)
    
    # Allow for small rounding differences
    assert abs(actual_bytes - expected_bytes) <= 1


@given(st.sampled_from(["0", "0B", "0KB", "0.0MB", "0.0GB"]))
def test_bytesize_zero_values(zero_str):
    """ByteSize should handle zero values in all formats"""
    class Model(BaseModel):
        size: ByteSize
    
    m = Model(size=zero_str)
    assert int(m.size) == 0
    assert m.size.to("B") == 0.0