"""Property-based tests for htmldate.cli module using Hypothesis."""
import sys
import os
from datetime import datetime, timedelta
from io import StringIO

# Add the htmldate path for imports
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the modules we're testing
from htmldate.cli import parse_args, cli_examine, process_args
from htmldate.validators import is_valid_format, is_valid_date, validate_and_convert
from htmldate.utils import is_wrong_document


# Property 1: is_valid_format should correctly validate format strings
@given(st.text())
def test_is_valid_format_property(format_string):
    """Test that is_valid_format correctly identifies valid/invalid format strings."""
    result = is_valid_format(format_string)
    
    # If it returns True, the format should be usable with strftime
    if result:
        # Verify by trying to use it
        test_date = datetime(2020, 1, 1)
        try:
            test_date.strftime(format_string)
            assert True  # Format is indeed valid
        except (ValueError, TypeError):
            assert False, f"is_valid_format returned True for invalid format: {format_string}"
    
    # If it contains %, it might be a format string
    if "%" in format_string and result:
        # It should be a valid strftime format
        test_date = datetime(2020, 1, 1)
        try:
            test_date.strftime(format_string)
        except (ValueError, TypeError):
            assert False, f"Format with % marked as valid but fails: {format_string}"


# Property 2: Date validation boundaries should be respected
@given(
    st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31)),
    st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31)),
    st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31))
)
def test_date_validation_boundaries(date_to_test, min_date, max_date):
    """Test that date validation correctly respects min and max boundaries."""
    # Ensure min_date <= max_date for valid test
    if min_date > max_date:
        min_date, max_date = max_date, min_date
    
    date_str = date_to_test.strftime("%Y-%m-%d")
    result = is_valid_date(date_str, "%Y-%m-%d", min_date, max_date)
    
    # The result should be True iff date is within boundaries
    expected = min_date <= date_to_test <= max_date
    assert result == expected, f"Date {date_str} validation incorrect with bounds [{min_date}, {max_date}]"


# Property 3: validate_and_convert round-trip property
@given(
    st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2099, 12, 31))
)
def test_validate_and_convert_round_trip(date_input):
    """Test that validate_and_convert maintains consistency."""
    # Use reasonable boundaries
    min_date = datetime(1900, 1, 1)
    max_date = datetime(2100, 1, 1)
    
    # Test with standard format
    date_str = date_input.strftime("%Y-%m-%d")
    result = validate_and_convert(date_str, "%Y-%m-%d", min_date, max_date)
    
    if result is not None:
        # Parse it back and verify it matches
        parsed = datetime.strptime(result, "%Y-%m-%d")
        assert parsed.date() == date_input.date(), f"Round-trip failed: {date_input} -> {result} -> {parsed}"


# Property 4: parse_args should handle various argument combinations
@given(
    st.booleans(),  # fast
    st.one_of(st.none(), st.text(min_size=1)),  # inputfile
    st.booleans(),  # original
    st.one_of(st.none(), st.text(min_size=1)),  # URL
    st.booleans(),  # verbose
)
def test_parse_args_combinations(fast, inputfile, original, url, verbose):
    """Test that parse_args handles various argument combinations correctly."""
    args = []
    
    if not fast:  # fast is store_false, so we add flag when we want False
        args.append("--fast")
    
    if inputfile:
        args.extend(["-i", inputfile])
    
    if original:
        args.append("--original")
    
    if url:
        args.extend(["-u", url])
    
    if verbose:
        args.append("-v")
    
    # Parse the arguments
    parsed = parse_args(args)
    
    # Verify the parsed arguments match expectations
    assert parsed.fast == fast
    assert parsed.original == original
    assert parsed.verbose == verbose
    
    # These might be None or the provided value
    if inputfile:
        assert parsed.inputfile == inputfile
    if url:
        assert parsed.URL == url


# Property 5: is_wrong_document should consistently identify problematic documents
@given(st.one_of(
    st.none(),
    st.text(max_size=10000000),  # Normal sized documents
    st.text(min_size=10000001, max_size=10000010),  # Too large documents
))
def test_is_wrong_document_property(data):
    """Test that is_wrong_document correctly identifies problematic input."""
    result = is_wrong_document(data)
    
    # Check the logic matches the implementation
    if data is None or not data:
        assert result == True, "Should reject None or empty data"
    elif len(data) > 10000000:  # MAX_FILE_SIZE from settings
        assert result == True, "Should reject too large documents"
    else:
        assert result == False, "Should accept normal-sized documents"


# Property 6: CLI examine should never crash on valid HTML input
@given(st.text(min_size=1, max_size=1000))
@settings(max_examples=100)
def test_cli_examine_no_crash(html_content):
    """Test that cli_examine doesn't crash on various HTML inputs."""
    # Create a mock args object
    class MockArgs:
        fast = False
        original = False
        verbose = False
        mindate = None
        maxdate = None
    
    args = MockArgs()
    
    # This should not raise an exception
    try:
        result = cli_examine(html_content, args)
        # Result should be None or a string
        assert result is None or isinstance(result, str)
    except Exception as e:
        # Check if it's an expected error
        if "document is empty or too large" not in str(e):
            raise


# Property 7: Date format strings with % should be validated consistently
@given(st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"], whitelist_characters="-%")))
def test_format_string_with_percent(format_str):
    """Test format strings containing % are validated consistently."""
    # Add % to make it look like a format string
    if format_str and "%" not in format_str:
        format_str = "%" + format_str
    
    result = is_valid_format(format_str)
    
    # Try to actually use the format
    test_date = datetime(2020, 6, 15)
    try:
        formatted = test_date.strftime(format_str)
        # If strftime succeeds, is_valid_format should return True
        assert result == True, f"Format {format_str} works but marked invalid"
    except (ValueError, TypeError):
        # If strftime fails, is_valid_format should return False 
        # (unless it's being more permissive for some reason)
        pass  # Can't assert False here as is_valid_format might be more strict


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])