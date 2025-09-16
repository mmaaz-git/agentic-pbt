import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

import re
from hypothesis import given, strategies as st, assume
from hypothesis import settings
from prompt_toolkit.validation import ValidationError

from InquirerPy.validator import NumberValidator, PasswordValidator, EmptyInputValidator
from InquirerPy.separator import Separator
from InquirerPy.resolver import _get_questions

class FakeDocument:
    """Mock document for testing validators."""
    def __init__(self, text):
        self.text = text
        self.cursor_position = len(text)


# Test 1: NumberValidator integer validation
@given(st.text())
def test_number_validator_integer_only(text):
    """NumberValidator with float_allowed=False should only accept valid integers."""
    validator = NumberValidator(float_allowed=False)
    doc = FakeDocument(text)
    
    try:
        validator.validate(doc)
        # If validation passes, text should be a valid integer
        int_value = int(text)
        assert str(int_value) == text or (text.startswith('+') and str(int_value) == text[1:]) or (text.startswith('-0') and int_value == 0)
    except ValidationError:
        # If validation fails, text should not be convertible to int
        try:
            int(text)
            assert False, f"Validator rejected valid integer: {text!r}"
        except ValueError:
            pass  # Expected


# Test 2: NumberValidator float validation
@given(st.text())
def test_number_validator_float_allowed(text):
    """NumberValidator with float_allowed=True should accept valid floats and integers."""
    validator = NumberValidator(float_allowed=True)
    doc = FakeDocument(text)
    
    try:
        validator.validate(doc)
        # If validation passes, text should be a valid float
        float_value = float(text)
        # No assertion failure means the property holds
    except ValidationError:
        # If validation fails, text should not be convertible to float
        try:
            float(text)
            assert False, f"Validator rejected valid float: {text!r}"
        except ValueError:
            pass  # Expected


# Test 3: EmptyInputValidator invariant
@given(st.text())
def test_empty_input_validator(text):
    """EmptyInputValidator should reject empty strings and accept non-empty strings."""
    validator = EmptyInputValidator()
    doc = FakeDocument(text)
    
    try:
        validator.validate(doc)
        # If validation passes, text should be non-empty
        assert len(text) > 0
    except ValidationError:
        # If validation fails, text should be empty
        assert len(text) == 0


# Test 4: PasswordValidator regex compilation
@given(
    length=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
    cap=st.booleans(),
    special=st.booleans(),
    number=st.booleans()
)
def test_password_validator_regex_construction(length, cap, special, number):
    """PasswordValidator should construct valid regex patterns based on constraints."""
    # This tests that the regex pattern is correctly constructed
    validator = PasswordValidator(length=length, cap=cap, special=special, number=number)
    
    # The validator should have a compiled regex
    assert hasattr(validator, '_re')
    assert isinstance(validator._re, type(re.compile('')))
    
    # Test some specific passwords to verify the regex works as expected
    test_cases = []
    
    # Build a password that should pass
    valid_password = ""
    if cap:
        valid_password += "A"
    if special:
        valid_password += "@"
    if number:
        valid_password += "1"
    
    # Pad to minimum length
    if length:
        while len(valid_password) < length:
            valid_password += "a"
    else:
        valid_password += "a"  # At least one char if no length requirement
    
    doc = FakeDocument(valid_password)
    
    # This password should pass validation
    try:
        validator.validate(doc)
    except ValidationError:
        # The constructed password should always pass
        assert False, f"Valid password rejected: {valid_password!r} with constraints: length={length}, cap={cap}, special={special}, number={number}"


# Test 5: Separator string representation invariant
@given(st.text())
def test_separator_string_representation(line):
    """Separator's string representation should match its line parameter."""
    separator = Separator(line)
    assert str(separator) == line


# Test 6: _get_questions dict to list conversion
@given(
    st.dictionaries(
        st.text(min_size=1),
        st.one_of(st.text(), st.integers(), st.booleans(), st.none())
    )
)
def test_get_questions_dict_to_list(question_dict):
    """_get_questions should convert a dict to a list with one element."""
    result = _get_questions(question_dict)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == question_dict


# Test 7: _get_questions list passthrough
@given(
    st.lists(
        st.dictionaries(
            st.text(min_size=1),
            st.one_of(st.text(), st.integers(), st.booleans(), st.none())
        )
    )
)
def test_get_questions_list_passthrough(questions_list):
    """_get_questions should return lists unchanged."""
    result = _get_questions(questions_list)
    assert result == questions_list
    assert result is questions_list  # Should be the same object


# Test 8: Password validation with generated passwords
@given(st.text())
def test_password_validator_acceptance(password):
    """Test that PasswordValidator correctly validates passwords against its constraints."""
    # Test with all constraints enabled
    validator = PasswordValidator(length=8, cap=True, special=True, number=True)
    doc = FakeDocument(password)
    
    try:
        validator.validate(doc)
        # If validation passes, check all constraints are met
        assert len(password) >= 8, f"Password {password!r} is too short but passed validation"
        assert any(c.isupper() for c in password), f"Password {password!r} has no uppercase but passed validation"
        assert any(c in "@$!%*#?&" for c in password), f"Password {password!r} has no special char but passed validation"
        assert any(c.isdigit() for c in password), f"Password {password!r} has no digit but passed validation"
    except ValidationError:
        # If validation fails, at least one constraint should be violated
        constraint_violations = []
        if len(password) < 8:
            constraint_violations.append("too short")
        if not any(c.isupper() for c in password):
            constraint_violations.append("no uppercase")
        if not any(c in "@$!%*#?&" for c in password):
            constraint_violations.append("no special char")
        if not any(c.isdigit() for c in password):
            constraint_violations.append("no digit")
        
        assert constraint_violations, f"Password {password!r} meets all constraints but was rejected"


# Test 9: NumberValidator edge cases with special float representations
@given(st.sampled_from(["inf", "-inf", "nan", "NaN", "infinity", "-infinity", "+inf", "Infinity"]))
def test_number_validator_special_floats(special_value):
    """NumberValidator should handle special float values consistently."""
    validator = NumberValidator(float_allowed=True)
    doc = FakeDocument(special_value)
    
    # Python's float() accepts these special values
    try:
        float_val = float(special_value)
        # Validator should also accept them
        try:
            validator.validate(doc)
        except ValidationError:
            assert False, f"Validator rejected valid float representation: {special_value!r}"
    except ValueError:
        # If Python's float() rejects it, validator should too
        try:
            validator.validate(doc)
            assert False, f"Validator accepted invalid float: {special_value!r}"
        except ValidationError:
            pass  # Expected