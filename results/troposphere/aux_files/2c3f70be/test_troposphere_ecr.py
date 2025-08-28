import troposphere.ecr as ecr
from hypothesis import given, strategies as st, assume
import pytest


@given(st.sampled_from(['true', 'True', 'false', 'False']))
def test_boolean_case_variations_should_work(base_value):
    """Test that common case variations of boolean strings should be accepted.
    
    The boolean function accepts 'true', 'True', 'false', and 'False'.
    It's reasonable to expect that common variations like 'TRUE' and 'FALSE'
    should also work, as these are standard boolean string representations.
    """
    # Test uppercase variant
    upper_value = base_value.upper()
    
    # The function accepts 'true' and 'True', so 'TRUE' should also work
    # Similarly for 'false', 'False', and 'FALSE'
    try:
        result = ecr.boolean(upper_value)
        # If it works, it should return the expected boolean
        if base_value.lower() == 'true':
            assert result is True
        else:
            assert result is False
    except ValueError:
        # This demonstrates the inconsistency - accepts mixed case but not all uppercase
        pytest.fail(f"boolean() accepts '{base_value}' but rejects '{upper_value}' - inconsistent case handling")


@given(st.sampled_from([True, False, 1, 0, '1', '0', 'true', 'false', 'True', 'False']))  
def test_boolean_idempotence(value):
    """Test that applying boolean twice gives the same result as applying it once."""
    first_result = ecr.boolean(value)
    # The result should be a boolean that is also accepted by the function
    second_result = ecr.boolean(first_result)
    assert first_result == second_result


@given(st.text(min_size=1, max_size=20))
def test_boolean_accepts_common_boolean_representations(text):
    """Test that boolean function handles common boolean string representations consistently."""
    # Filter to only test boolean-like strings
    assume(text.lower() in ['true', 'false', 'yes', 'no', 'on', 'off', '1', '0', 't', 'f', 'y', 'n'])
    
    # For common boolean representations, the function should either:
    # 1. Accept all common variations of true/false consistently
    # 2. Or reject them all consistently
    
    lower_text = text.lower()
    
    # Group related representations
    true_variants = ['true', 't', 'yes', 'y', 'on', '1']
    false_variants = ['false', 'f', 'no', 'n', 'off', '0']
    
    if lower_text in true_variants:
        # Test case variations
        for case_variant in [text.lower(), text.upper(), text.capitalize()]:
            try:
                result = ecr.boolean(case_variant)
                # If one case works, all cases should work for consistency
                if case_variant != text:
                    try:
                        other_result = ecr.boolean(text)
                        assert result == other_result, f"Inconsistent results for case variations of {text}"
                    except ValueError:
                        pytest.fail(f"Inconsistent case handling: accepts {case_variant} but not {text}")
            except ValueError:
                pass  # This variant doesn't work, which is fine if consistent


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers()
))
def test_boolean_numeric_consistency(num):
    """Test that boolean handles numeric values consistently."""
    # The function accepts 0, 1, 0.0, 1.0
    # It should handle numeric types consistently
    
    if num == 0 or num == 0.0:
        result = ecr.boolean(num)
        assert result is False
    elif num == 1 or num == 1.0:
        result = ecr.boolean(num)
        assert result is True
    else:
        # Other numbers should raise ValueError
        with pytest.raises(ValueError):
            ecr.boolean(num)