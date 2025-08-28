"""Focused test to demonstrate the comma parsing bug in fire.interact."""

import types
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
from fire import interact
from hypothesis import given, strategies as st


@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_'), min_size=1, max_size=10))
def test_comma_in_variable_names(base_name):
    """Test that variable names containing commas are handled correctly."""
    # Create a variable name with comma
    var_with_comma = base_name + ',' + base_name
    
    variables = {
        'normal_var': 1,
        var_with_comma: 2,
        'another_var': 3
    }
    
    output = interact._AvailableString(variables, verbose=False)
    
    # Try to parse the output
    lines = output.split('\n')
    for line in lines:
        if 'Objects:' in line and ':' in line:
            items_str = line.split(':', 1)[1].strip()
            if items_str:
                # Split by comma to get individual items
                parsed_items = [item.strip() for item in items_str.split(',')]
                
                # The bug: we expect 3 items, but get more due to comma in variable name
                # This creates ambiguous output
                expected_items = {'normal_var', var_with_comma, 'another_var'}
                parsed_set = set(parsed_items)
                
                # Check if parsing recovers original variable names
                if parsed_set != expected_items:
                    print(f"BUG FOUND: Variable name with comma causes parsing ambiguity")
                    print(f"Original variables: {expected_items}")
                    print(f"Parsed as: {parsed_set}")
                    print(f"Raw output line: {line}")
                    assert False, f"Comma in variable name '{var_with_comma}' breaks output parsing"


if __name__ == '__main__':
    # Run with a specific example
    import pytest
    pytest.main([__file__, '-v', '-s'])