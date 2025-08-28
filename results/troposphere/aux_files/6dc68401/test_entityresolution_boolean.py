"""Property-based tests for troposphere.entityresolution.boolean function."""

import string
from hypothesis import assume, given, strategies as st
from hypothesis import settings
import troposphere.entityresolution as er


# Strategy for valid boolean inputs (based on code inspection)
valid_true_inputs = st.sampled_from([True, 1, "1", "true", "True"])
valid_false_inputs = st.sampled_from([False, 0, "0", "false", "False"])
valid_inputs = st.one_of(valid_true_inputs, valid_false_inputs)


@given(valid_inputs)
def test_boolean_returns_bool_type(x):
    """Test that boolean() always returns a bool type for valid inputs."""
    result = er.boolean(x)
    assert isinstance(result, bool), f"boolean({repr(x)}) returned {type(result).__name__}, expected bool"


@given(valid_inputs)
def test_boolean_idempotence(x):
    """Test that boolean(boolean(x)) == boolean(x) for valid inputs."""
    first_result = er.boolean(x)
    second_result = er.boolean(first_result)
    assert second_result == first_result, f"boolean(boolean({repr(x)})) != boolean({repr(x)})"


@given(valid_true_inputs, valid_false_inputs)
def test_true_false_mutual_exclusivity(true_val, false_val):
    """Test that values returning True never return False and vice versa."""
    assert er.boolean(true_val) == True
    assert er.boolean(false_val) == False
    # They should never be equal
    assert er.boolean(true_val) != er.boolean(false_val)


@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10))
def test_case_variations_of_true_false(text):
    """Test case handling for variations of 'true' and 'false'."""
    # The function handles "true", "True" but we want to test if other cases work
    if text.lower() == "true":
        # Test different case variations
        if text in ["true", "True"]:
            # These should work
            assert er.boolean(text) == True
        else:
            # Other variations like "TRUE", "tRue", etc. should raise ValueError
            try:
                result = er.boolean(text)
                # If it doesn't raise, it might be a bug if the result is unexpected
                if text.upper() == "TRUE" and text not in ["true", "True"]:
                    # This is the potential bug - "TRUE" should perhaps work but doesn't
                    assert False, f"boolean({repr(text)}) returned {result} but 'TRUE' variant was expected to raise ValueError"
            except ValueError:
                pass  # Expected for variations not in the list
    elif text.lower() == "false":
        if text in ["false", "False"]:
            assert er.boolean(text) == False
        else:
            try:
                result = er.boolean(text)
                if text.upper() == "FALSE" and text not in ["false", "False"]:
                    assert False, f"boolean({repr(text)}) returned {result} but 'FALSE' variant was expected to raise ValueError"
            except ValueError:
                pass


@given(st.one_of(
    st.integers(min_value=2, max_value=100),  # integers other than 0, 1
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=1).filter(lambda x: x not in ["true", "True", "false", "False", "1", "0"]),
    st.none(),
    st.lists(st.integers())
))
def test_invalid_inputs_raise_valueerror(x):
    """Test that invalid inputs raise ValueError."""
    try:
        result = er.boolean(x)
        # If we get here without exception, check if it's an unexpected accepted value
        assert False, f"boolean({repr(x)}) returned {result} but was expected to raise ValueError"
    except ValueError:
        pass  # Expected
    except Exception as e:
        assert False, f"boolean({repr(x)}) raised {type(e).__name__} instead of ValueError"


@given(st.sampled_from(["TRUE", "FALSE", "True", "False", "true", "false"]))
def test_case_sensitivity_consistency(text):
    """Test that case handling is consistent - if 'True' works, should 'TRUE' work too?"""
    if text in ["true", "True", "false", "False"]:
        # These should work according to the implementation
        result = er.boolean(text)
        assert isinstance(result, bool)
    else:
        # "TRUE" and "FALSE" don't work - this might be a bug
        try:
            result = er.boolean(text)
            assert False, f"boolean({repr(text)}) unexpectedly returned {result}"
        except ValueError:
            # This is what happens, but it's inconsistent
            # The function accepts "True" but not "TRUE"
            pass


@given(st.sampled_from([1, "1", True, "true", "True"]))
def test_truthy_values_consistency(x):
    """All truthy values should return True."""
    assert er.boolean(x) == True


@given(st.sampled_from([0, "0", False, "false", "False"]))
def test_falsy_values_consistency(x):
    """All falsy values should return False."""
    assert er.boolean(x) == False