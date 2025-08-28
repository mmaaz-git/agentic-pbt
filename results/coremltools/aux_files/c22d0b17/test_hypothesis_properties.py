#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from quickbooks import utils
import re


@given(st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.one_of(
        st.text(max_size=100),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False)
    ),
    min_size=1,
    max_size=10
))
@settings(max_examples=1000)
def test_build_where_clause_comprehensive(params):
    """Comprehensive test for SQL injection protection in build_where_clause"""
    where_clause = utils.build_where_clause(**params)
    
    # Check that all string values with quotes are escaped
    for key, value in params.items():
        if isinstance(value, str) and "'" in value:
            # The original quote should be escaped in the output
            # Look for the pattern: key = 'value' where value contains escaped quotes
            pattern = f"{key} = '.*\\\\''.*'"
            if not re.search(pattern, where_clause):
                # Let's check more carefully
                expected_escaped = value.replace("'", r"\'")
                expected_clause = f"{key} = '{expected_escaped}'"
                if expected_clause not in where_clause:
                    print(f"\nFAILURE FOUND!")
                    print(f"Input: {key} = {repr(value)}")
                    print(f"Expected escaped value: {repr(expected_escaped)}")
                    print(f"Expected in output: {expected_clause}")
                    print(f"Actual output: {where_clause}")
                    assert False, f"Quote not properly escaped for {key}={value}"


@given(st.lists(
    st.one_of(
        st.text(max_size=100),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False)
    ),
    min_size=1,
    max_size=20
), st.text(min_size=1, max_size=50))
@settings(max_examples=1000)
def test_build_choose_clause_comprehensive(choices, field):
    """Comprehensive test for SQL injection protection in build_choose_clause"""
    where_clause = utils.build_choose_clause(choices, field)
    
    # Check that all string choices with quotes are escaped
    for choice in choices:
        if isinstance(choice, str) and "'" in choice:
            expected_escaped = choice.replace("'", r"\'")
            if expected_escaped not in where_clause:
                print(f"\nFAILURE FOUND!")
                print(f"Choice: {repr(choice)}")
                print(f"Field: {field}")
                print(f"Expected escaped: {repr(expected_escaped)}")
                print(f"Actual output: {where_clause}")
                assert False, f"Quote not properly escaped for choice={choice}"


@given(st.text())
@settings(max_examples=1000)
def test_single_quote_edge_cases(text):
    """Test edge cases with various quote patterns"""
    params = {"field": text}
    where_clause = utils.build_where_clause(**params)
    
    # Count quotes in input
    input_quotes = text.count("'")
    
    if input_quotes > 0:
        # All input quotes should be escaped
        escaped_text = text.replace("'", r"\'")
        expected = f"field = '{escaped_text}'"
        
        if expected != where_clause:
            print(f"\nFAILURE FOUND!")
            print(f"Input text: {repr(text)}")
            print(f"Expected: {expected}")
            print(f"Actual: {where_clause}")
            assert False, f"Escaping failed for text={text}"


@given(st.text(alphabet=st.characters(categories=["Cc", "Cs", "Co"])))
@settings(max_examples=100)
def test_control_characters(text):
    """Test with control characters and special Unicode"""
    if not text:
        return
    
    params = {"field": text}
    try:
        where_clause = utils.build_where_clause(**params)
        # Should handle control characters without crashing
        assert "field = " in where_clause
    except Exception as e:
        print(f"\nCRASH FOUND!")
        print(f"Input text: {repr(text)}")
        print(f"Exception: {e}")
        raise


def run_hypothesis_tests():
    print("Running Hypothesis property-based tests...")
    print("=" * 60)
    
    print("\n1. Testing build_where_clause with comprehensive inputs...")
    try:
        test_build_where_clause_comprehensive()
        print("✓ Passed 1000 examples")
    except AssertionError as e:
        print(f"✗ Bug found: {e}")
        return False
    
    print("\n2. Testing build_choose_clause with comprehensive inputs...")
    try:
        test_build_choose_clause_comprehensive()
        print("✓ Passed 1000 examples")
    except AssertionError as e:
        print(f"✗ Bug found: {e}")
        return False
    
    print("\n3. Testing single quote edge cases...")
    try:
        test_single_quote_edge_cases()
        print("✓ Passed 1000 examples")
    except AssertionError as e:
        print(f"✗ Bug found: {e}")
        return False
    
    print("\n4. Testing control characters...")
    try:
        test_control_characters()
        print("✓ Passed 100 examples")
    except Exception as e:
        print(f"✗ Bug found: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All property-based tests passed!")
    return True


if __name__ == "__main__":
    success = run_hypothesis_tests()
    sys.exit(0 if success else 1)