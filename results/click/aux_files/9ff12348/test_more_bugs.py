import click.types
from hypothesis import given, strategies as st, assume
import uuid as uuid_module


@given(st.text())
def test_uuid_strip_inconsistency(value):
    """Test UUID parameter stripping behavior"""
    uuid_type = click.types.UUIDParameterType()
    
    # Generate a valid UUID string with whitespace
    valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
    
    if value.strip() == valid_uuid:
        # Test with leading/trailing whitespace
        with_spaces = f"  {valid_uuid}  "
        result = uuid_type.convert(with_spaces, None, None)
        assert str(result) == valid_uuid
        
        # Test that strip is applied
        result2 = uuid_type.convert(value, None, None)
        assert str(result2) == valid_uuid


@given(st.text())
def test_bool_strip_inconsistency(value):
    """Test bool parameter stripping behavior"""
    bool_type = click.types.BoolParamType()
    
    # The code strips the value but doesn't handle all whitespace consistently
    if value.strip().lower() in {"true", "false", "1", "0", "yes", "no", "y", "n", "on", "off", "t", "f"}:
        try:
            result = bool_type.convert(value, None, None)
            assert isinstance(result, bool)
        except AttributeError as e:
            # If value is not a string, .strip() will fail
            print(f"BUG: BoolParamType failed on non-string: {value}")
            raise


@given(st.sampled_from([1, 0, True, False]))
def test_bool_non_string_bug(value):
    """Test that BoolParamType incorrectly handles non-string boolean values"""
    bool_type = click.types.BoolParamType()
    
    # Line 667-668: if value in {False, True}: return bool(value)
    # But line 670: norm = value.strip().lower()
    # This will fail for non-string values that aren't exactly True/False
    
    result = bool_type.convert(value, None, None)
    
    if value in {1, True}:
        assert result is True
    elif value in {0, False}:
        assert result is False


@given(st.integers())
def test_bool_integer_crash(value):
    """Test that BoolParamType crashes on integer inputs other than bool"""
    bool_type = click.types.BoolParamType()
    
    if value not in {0, 1, True, False}:
        try:
            result = bool_type.convert(value, None, None)
            # Should either work or raise BadParameter, not AttributeError
        except AttributeError as e:
            print(f"BUG FOUND: BoolParamType crashed with AttributeError on integer {value}")
            print(f"Error: {e}")
            assert False, f"BoolParamType should handle integer {value} gracefully"
        except click.types.BadParameter:
            pass  # This is expected


# Direct test
def test_bool_integer_bug_direct():
    """Direct test of BoolParamType integer handling bug"""
    bool_type = click.types.BoolParamType()
    
    # Test integer that's not 0 or 1
    test_value = 42
    
    try:
        result = bool_type.convert(test_value, None, None)
        print(f"Result for {test_value}: {result}")
    except AttributeError as e:
        print(f"BUG CONFIRMED: BoolParamType.convert({test_value}) raised AttributeError: {e}")
        print("This happens because line 670 calls .strip() on a non-string value")
        return True
    except click.types.BadParameter as e:
        print(f"Correctly raised BadParameter: {e}")
        return False
    
    return False


if __name__ == "__main__":
    if test_bool_integer_bug_direct():
        print("\n✗ Bug found: BoolParamType crashes on integer inputs")