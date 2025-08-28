#!/usr/bin/env python3
"""Focused hypothesis tests to find bugs in InquirerPy."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, reproduce_failure
from hypothesis.strategies import composite
import traceback

# Import components to test
from InquirerPy.validator import NumberValidator, PasswordValidator
from InquirerPy.resolver import _get_questions
from InquirerPy.separator import Separator
from prompt_toolkit.validation import ValidationError

class FakeDocument:
    def __init__(self, text):
        self.text = text
        self.cursor_position = len(text)


def run_test(test_func, test_name, max_examples=200):
    """Run a single hypothesis test and report results."""
    print(f"\nTesting: {test_name}")
    print("-" * 50)
    
    try:
        with settings(max_examples=max_examples):
            test_func()
        print(f"✓ PASSED: No bugs found after {max_examples} examples")
        return None
    except AssertionError as e:
        print(f"✗ FAILED: Bug found!")
        print(f"  {e}")
        return e
    except Exception as e:
        print(f"✗ ERROR: Unexpected exception")
        print(f"  {type(e).__name__}: {e}")
        traceback.print_exc()
        return e


# Bug Hunt 1: NumberValidator edge cases
@given(st.text())
def test_number_validator_consistency(text):
    """NumberValidator should be consistent with Python's int() and float()."""
    int_validator = NumberValidator(float_allowed=False)
    float_validator = NumberValidator(float_allowed=True)
    doc = FakeDocument(text)
    
    # Check integer validator
    try:
        int_validator.validate(doc)
        validator_accepts_int = True
    except ValidationError:
        validator_accepts_int = False
    
    try:
        int(text)
        python_accepts_int = True
    except (ValueError, OverflowError):
        python_accepts_int = False
    
    if validator_accepts_int != python_accepts_int:
        raise AssertionError(
            f"Integer validator inconsistent with Python int(): "
            f"text={text!r}, validator={validator_accepts_int}, Python={python_accepts_int}"
        )
    
    # Check float validator
    try:
        float_validator.validate(doc)
        validator_accepts_float = True
    except ValidationError:
        validator_accepts_float = False
    
    try:
        float(text)
        python_accepts_float = True
    except (ValueError, OverflowError):
        python_accepts_float = False
    
    if validator_accepts_float != python_accepts_float:
        raise AssertionError(
            f"Float validator inconsistent with Python float(): "
            f"text={text!r}, validator={validator_accepts_float}, Python={python_accepts_float}"
        )


# Bug Hunt 2: PasswordValidator with empty password
@given(
    length=st.integers(min_value=0, max_value=10),
    cap=st.booleans(),
    special=st.booleans(),
    number=st.booleans()
)
def test_password_validator_empty_string(length, cap, special, number):
    """Test PasswordValidator with empty string."""
    validator = PasswordValidator(length=length, cap=cap, special=special, number=number)
    doc = FakeDocument("")
    
    # An empty password should fail if any constraint is specified
    should_fail = length and length > 0 or cap or special or number
    
    try:
        validator.validate(doc)
        if should_fail:
            raise AssertionError(
                f"Empty password accepted with constraints: "
                f"length={length}, cap={cap}, special={special}, number={number}"
            )
    except ValidationError:
        if not should_fail and length == 0:
            # If length is explicitly 0 and no other constraints, empty should pass
            raise AssertionError(
                f"Empty password rejected with zero constraints: "
                f"length={length}, cap={cap}, special={special}, number={number}"
            )


# Bug Hunt 3: PasswordValidator regex edge cases
@given(st.text(min_size=1, max_size=50))
def test_password_validator_special_chars(password):
    """Test that special character validation works correctly."""
    validator = PasswordValidator(special=True)
    doc = FakeDocument(password)
    
    has_special = any(c in "@$!%*#?&" for c in password)
    
    try:
        validator.validate(doc)
        if not has_special:
            raise AssertionError(
                f"Password without special chars accepted: {password!r}"
            )
    except ValidationError:
        if has_special:
            raise AssertionError(
                f"Password with special char rejected: {password!r}"
            )


# Bug Hunt 4: _get_questions with edge case inputs
@given(st.integers())
def test_get_questions_invalid_type(value):
    """_get_questions should reject non-dict, non-list inputs."""
    from InquirerPy.exceptions import InvalidArgument
    
    try:
        result = _get_questions(value)
        raise AssertionError(
            f"_get_questions accepted invalid type {type(value).__name__}: {value!r}"
        )
    except InvalidArgument:
        pass  # Expected


# Bug Hunt 5: NumberValidator with whitespace
@given(
    st.text(alphabet=" \t\n\r", min_size=1),
    st.text(alphabet="0123456789+-.", min_size=1),
    st.text(alphabet=" \t\n\r", min_size=0)
)
def test_number_validator_whitespace(prefix, number, suffix):
    """Test NumberValidator with whitespace around numbers."""
    text = prefix + number + suffix
    validator = NumberValidator(float_allowed=True)
    doc = FakeDocument(text)
    
    # Python's float() handles leading/trailing whitespace
    try:
        float_value = float(text)
        python_accepts = True
    except (ValueError, OverflowError):
        python_accepts = False
    
    try:
        validator.validate(doc)
        validator_accepts = True
    except ValidationError:
        validator_accepts = False
    
    if validator_accepts != python_accepts:
        raise AssertionError(
            f"Whitespace handling mismatch: text={text!r}, "
            f"validator={validator_accepts}, Python={python_accepts}"
        )


# Bug Hunt 6: PasswordValidator with length=0
@given(st.text(max_size=20))
def test_password_validator_zero_length(password):
    """Test PasswordValidator with length=0."""
    validator = PasswordValidator(length=0)
    doc = FakeDocument(password)
    
    # With length=0, any password should be accepted (including empty)
    try:
        validator.validate(doc)
    except ValidationError:
        raise AssertionError(
            f"Password rejected with length=0: {password!r}"
        )


def main():
    """Run all bug hunting tests."""
    print("=" * 60)
    print("InquirerPy Property-Based Bug Hunt")
    print("=" * 60)
    
    tests = [
        (test_number_validator_consistency, "NumberValidator consistency with Python"),
        (test_password_validator_empty_string, "PasswordValidator with empty string"),
        (test_password_validator_special_chars, "PasswordValidator special characters"),
        (test_get_questions_invalid_type, "_get_questions type validation"),
        (test_number_validator_whitespace, "NumberValidator whitespace handling"),
        (test_password_validator_zero_length, "PasswordValidator with length=0"),
    ]
    
    bugs_found = []
    
    for test_func, test_name in tests:
        error = run_test(test_func, test_name)
        if error:
            bugs_found.append((test_name, error))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if bugs_found:
        print(f"\n✗ Found {len(bugs_found)} potential bug(s):")
        for test_name, error in bugs_found:
            print(f"  - {test_name}")
            print(f"    {str(error)[:100]}...")
    else:
        print("\n✓ All tests passed - no bugs found!")
    
    return len(bugs_found) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)