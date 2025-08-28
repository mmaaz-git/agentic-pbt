#!/usr/bin/env python3
"""Property-based test that discovered the output format ambiguity bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import io
from hypothesis import given, strategies as st, assume, example
from pyct.report import report


@given(st.text(min_size=1))
@example("package # comment")
@example("test # another # test")
def test_output_format_should_be_unambiguously_parseable(package_name):
    """The output format should be unambiguously parseable when split by ' # '"""
    assume('\x00' not in package_name)
    assume('\n' not in package_name)
    assume('\r' not in package_name)
    
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(package_name)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue().strip()
    
    # The format is documented as: "package=version # location"
    # This should be unambiguously parseable by splitting on ' # '
    parts = output.split(' # ')
    
    # We should get exactly 2 parts: [package=version, location]
    assert len(parts) == 2, f"Output format is ambiguous! Input '{package_name}' produced {len(parts)} parts instead of 2 when split by ' # ': {parts}"


if __name__ == "__main__":
    # Run the test to demonstrate the bug
    test_output_format_should_be_unambiguously_parseable()