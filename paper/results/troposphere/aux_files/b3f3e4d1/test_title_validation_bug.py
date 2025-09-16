#!/usr/bin/env python3
"""Test to demonstrate the title validation inconsistency bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import launchwizard
from hypothesis import given, strategies as st

# Test with Unicode letters that Python considers alphanumeric
unicode_alphanumeric = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
    min_size=1,
    max_size=50
).filter(lambda x: x.isalnum() and not x.isascii())

@given(title=unicode_alphanumeric)
def test_unicode_title_inconsistency(title):
    """
    Test that shows inconsistency between Python's isalnum() and troposphere's validation.
    
    The validate_title() method uses regex ^[a-zA-Z0-9]+$ which only accepts ASCII,
    but Python's isalnum() returns True for Unicode letters.
    
    This could be confusing for users who expect Unicode support.
    """
    # Python considers this alphanumeric
    assert title.isalnum(), f"{title} should be alphanumeric according to Python"
    
    # But troposphere rejects it
    try:
        deployment = launchwizard.Deployment(
            title,
            DeploymentPatternName="pattern",
            Name="name",
            WorkloadName="workload"
        )
        assert False, f"Expected ValueError for Unicode title '{title}'"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)
        # This shows the inconsistency - Python says it's alphanumeric,
        # but troposphere says it's not


def manual_test(title):
    """Manual test without hypothesis decorator"""
    # Python considers this alphanumeric
    assert title.isalnum(), f"{title} should be alphanumeric according to Python"
    
    # But troposphere rejects it
    try:
        deployment = launchwizard.Deployment(
            title,
            DeploymentPatternName="pattern",
            Name="name",
            WorkloadName="workload"
        )
        assert False, f"Expected ValueError for Unicode title '{title}'"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)


if __name__ == "__main__":
    # Run some explicit examples
    test_cases = ['µ', 'Ω', 'ñ', 'é', 'ü', 'ß', 'Δ', 'λ', 'π', '中文']
    
    for title in test_cases:
        if title.isalnum():
            print(f"Testing '{title}' (Python isalnum: {title.isalnum()})")
            try:
                manual_test(title)
                print(f"  ✓ Correctly rejected by troposphere")
            except AssertionError:
                print(f"  ✗ Unexpectedly accepted by troposphere")
    
    # Run property-based test with pytest
    import pytest
    print("\nTo run property-based test, use: pytest test_title_validation_bug.py")