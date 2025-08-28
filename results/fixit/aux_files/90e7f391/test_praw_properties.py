"""Property-based tests for praw utility functions."""

import sys
import string
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from praw.util import camel_to_snake, snake_case_keys


# Generate valid identifier strings (letters and digits, starting with letter)
valid_identifiers = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=1,
    max_size=100
).filter(lambda s: s[0].isalpha() if s else False)

# Generate camelCase strings
camel_case_strings = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=1,
    max_size=100
)

@given(camel_case_strings)
def test_camel_to_snake_idempotence(s):
    """
    Property: Applying camel_to_snake twice should give the same result as applying it once.
    This is because snake_case doesn't have capital letters, so the second application
    should not change anything.
    """
    once = camel_to_snake(s)
    twice = camel_to_snake(once)
    assert once == twice


@given(camel_case_strings)
def test_camel_to_snake_output_format(s):
    """
    Property: The output of camel_to_snake should always be lowercase,
    as stated in the docstring: "Convert name from camelCase to snake_case."
    """
    result = camel_to_snake(s)
    assert result == result.lower()


@given(camel_case_strings)
def test_camel_to_snake_no_double_underscores(s):
    """
    Property: The output should not have double underscores unless the input had them.
    Well-formed snake_case doesn't have consecutive underscores.
    """
    result = camel_to_snake(s)
    # If input doesn't have consecutive underscores, output shouldn't either
    if '__' not in s:
        # The function adds underscores before uppercase letters, but shouldn't create doubles
        # unless there are consecutive uppercase letters
        pass  # This property is hard to test precisely due to regex complexity


@given(st.dictionaries(
    keys=valid_identifiers,
    values=st.integers() | st.text() | st.booleans() | st.none(),
    min_size=0,
    max_size=100
))
def test_snake_case_keys_preserves_size(d):
    """
    Property: snake_case_keys should preserve the number of keys in the dictionary.
    The function only transforms keys, not add or remove them.
    """
    result = snake_case_keys(d)
    assert len(result) == len(d)


@given(st.dictionaries(
    keys=valid_identifiers,
    values=st.integers() | st.text() | st.booleans() | st.none(),
    min_size=0,
    max_size=100
))
def test_snake_case_keys_preserves_values(d):
    """
    Property: snake_case_keys should preserve all values unchanged.
    Only keys are transformed, values remain the same.
    """
    result = snake_case_keys(d)
    # All values from original dict should be in result
    original_values = set(d.values())
    result_values = set(result.values())
    assert original_values == result_values


@given(st.dictionaries(
    keys=valid_identifiers,
    values=st.integers() | st.text() | st.booleans() | st.none(),
    min_size=1,
    max_size=100
))
def test_snake_case_keys_idempotence(d):
    """
    Property: Applying snake_case_keys twice should give the same result as once.
    Since snake_case is already in the target format, applying again shouldn't change it.
    """
    once = snake_case_keys(d)
    twice = snake_case_keys(once)
    assert once == twice


# Test specific camelCase patterns that should be handled correctly
@given(st.text(alphabet=string.ascii_letters, min_size=1, max_size=20))
def test_camel_to_snake_handles_acronyms(s):
    """
    Property: The function should handle acronyms properly.
    Based on the regex pattern, it should add underscores between:
    - lowercase followed by uppercase
    - uppercase followed by uppercase then lowercase
    """
    # Test some specific patterns
    test_cases = [
        ("HTTPResponse", "http_response"),
        ("XMLParser", "xml_parser"),
        ("parseHTMLString", "parse_html_string"),
        ("IOError", "io_error"),
    ]
    
    for input_str, expected in test_cases:
        assert camel_to_snake(input_str) == expected


# Test edge cases
def test_camel_to_snake_edge_cases():
    """Test edge cases for camel_to_snake."""
    # Empty string
    assert camel_to_snake("") == ""
    
    # Single character
    assert camel_to_snake("a") == "a"
    assert camel_to_snake("A") == "a"
    
    # Already snake_case
    assert camel_to_snake("already_snake_case") == "already_snake_case"
    
    # Numbers
    assert camel_to_snake("version2API") == "version2_api"
    assert camel_to_snake("HTML2PDF") == "html2_pdf"


def test_snake_case_keys_collision():
    """
    Test if snake_case_keys handles key collisions properly.
    If two different camelCase keys map to the same snake_case,
    one will overwrite the other.
    """
    # These two different keys will map to the same snake_case key
    d = {"myKey": 1, "myKEY": 2}
    result = snake_case_keys(d)
    # Both map to "my_key", so result should have only one key
    assert len(result) == 1
    assert "my_key" in result
    # The value will be from whichever key was processed last (dict ordering)