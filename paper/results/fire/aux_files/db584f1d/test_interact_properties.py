"""Property-based tests for fire.interact module using Hypothesis."""

import inspect
import sys
import types
from hypothesis import given, strategies as st, assume, settings
import re

# Import the module under test
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
from fire import interact


# Strategy for generating valid Python variable names
def valid_var_name():
    """Generate valid Python variable names."""
    first_char = st.one_of(
        st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')),
        st.characters(min_codepoint=ord('A'), max_codepoint=ord('Z')),
        st.just('_')
    )
    other_chars = st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_'
        ),
        min_size=0,
        max_size=10
    )
    return st.builds(lambda f, o: f + o, first_char, other_chars)


# Strategy for generating variable names with special characters
def special_var_name():
    """Generate variable names that may contain special characters."""
    return st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        min_size=1,
        max_size=20
    ).filter(lambda s: s and not s.isspace())


# Strategy for generating mixed variable dictionaries
@st.composite
def variables_dict(draw):
    """Generate a dictionary of variables with mixed types."""
    n_vars = draw(st.integers(min_value=0, max_value=20))
    result = {}
    
    for _ in range(n_vars):
        # Generate variable name
        name_type = draw(st.integers(0, 3))
        if name_type == 0:  # Normal name
            name = draw(valid_var_name())
        elif name_type == 1:  # Name with underscore prefix
            name = '_' + draw(valid_var_name())
        elif name_type == 2:  # Name with dash or slash
            base = draw(valid_var_name())
            sep = draw(st.sampled_from(['-', '/']))
            suffix = draw(valid_var_name())
            name = base + sep + suffix
        else:  # Other special names
            name = draw(special_var_name())
        
        # Generate value
        value_type = draw(st.integers(0, 2))
        if value_type == 0:  # Module
            value = types.ModuleType(f'module_{name}')
        elif value_type == 1:  # Regular object
            value = draw(st.one_of(
                st.integers(),
                st.text(),
                st.lists(st.integers()),
                st.dictionaries(st.text(), st.integers()),
            ))
        else:  # Function
            value = lambda: None
        
        # Avoid duplicate keys
        if name not in result:
            result[name] = value
    
    return result


@given(variables_dict())
def test_underscore_filtering_when_not_verbose(variables):
    """Test that variables starting with _ are filtered when verbose=False."""
    output = interact._AvailableString(variables, verbose=False)
    
    # Extract variable names from output
    lines = output.split('\n')
    mentioned_vars = set()
    for line in lines:
        if 'Modules:' in line or 'Objects:' in line:
            # Extract the list part after the colon
            if ':' in line:
                items_str = line.split(':', 1)[1].strip()
                if items_str:
                    items = [item.strip() for item in items_str.split(',')]
                    mentioned_vars.update(items)
    
    # Check that no underscore-prefixed variables appear
    for var_name in mentioned_vars:
        assert not var_name.startswith('_'), f"Variable {var_name} starts with _ but appeared in non-verbose output"


@given(variables_dict())
def test_dash_slash_filtering(variables):
    """Test that variables with - or / in names are always filtered."""
    for verbose in [False, True]:
        output = interact._AvailableString(variables, verbose=verbose)
        
        # Extract variable names from output
        lines = output.split('\n')
        mentioned_vars = set()
        for line in lines:
            if 'Modules:' in line or 'Objects:' in line:
                if ':' in line:
                    items_str = line.split(':', 1)[1].strip()
                    if items_str:
                        items = [item.strip() for item in items_str.split(',')]
                        mentioned_vars.update(items)
        
        # Check that no variables with dash or slash appear
        for var_name in mentioned_vars:
            assert '-' not in var_name, f"Variable {var_name} contains - but appeared in output"
            assert '/' not in var_name, f"Variable {var_name} contains / but appeared in output"


@given(variables_dict())
def test_module_categorization(variables):
    """Test that modules are correctly categorized."""
    for verbose in [False, True]:
        output = interact._AvailableString(variables, verbose=verbose)
        
        # Parse output to extract modules and objects
        modules_set = set()
        objects_set = set()
        
        lines = output.split('\n')
        for line in lines:
            if 'Modules:' in line and ':' in line:
                items_str = line.split(':', 1)[1].strip()
                if items_str:
                    modules_set.update(item.strip() for item in items_str.split(','))
            elif 'Objects:' in line and ':' in line:
                items_str = line.split(':', 1)[1].strip()
                if items_str:
                    objects_set.update(item.strip() for item in items_str.split(','))
        
        # Check that modules are in the right category
        for name, value in variables.items():
            # Skip filtered names
            if '-' in name or '/' in name:
                continue
            if not verbose and name.startswith('_'):
                continue
            
            if inspect.ismodule(value):
                if name in objects_set:
                    assert False, f"Module {name} incorrectly categorized as Object"
                # It should be in modules_set if it appears at all
                if name in modules_set or name in objects_set:
                    assert name in modules_set, f"Module {name} not in Modules category"
            else:
                if name in modules_set:
                    assert False, f"Non-module {name} incorrectly categorized as Module"


@given(variables_dict())
def test_sorting_within_categories(variables):
    """Test that items within each category are sorted alphabetically."""
    for verbose in [False, True]:
        output = interact._AvailableString(variables, verbose=verbose)
        
        lines = output.split('\n')
        for line in lines:
            if ('Modules:' in line or 'Objects:' in line) and ':' in line:
                items_str = line.split(':', 1)[1].strip()
                if items_str:
                    items = [item.strip() for item in items_str.split(',')]
                    if len(items) > 1:
                        # Check if sorted
                        sorted_items = sorted(items)
                        assert items == sorted_items, f"Items not sorted: {items} != {sorted_items}"


@given(variables_dict())
def test_no_duplicate_entries(variables):
    """Test that no variable appears more than once in the output."""
    for verbose in [False, True]:
        output = interact._AvailableString(variables, verbose=verbose)
        
        # Extract all variable names
        all_mentioned = []
        lines = output.split('\n')
        for line in lines:
            if ('Modules:' in line or 'Objects:' in line) and ':' in line:
                items_str = line.split(':', 1)[1].strip()
                if items_str:
                    items = [item.strip() for item in items_str.split(',')]
                    all_mentioned.extend(items)
        
        # Check for duplicates
        seen = set()
        for var in all_mentioned:
            assert var not in seen, f"Variable {var} appears multiple times in output"
            seen.add(var)


@given(variables_dict())
def test_output_format(variables):
    """Test that the output format is consistent."""
    for verbose in [False, True]:
        output = interact._AvailableString(variables, verbose=verbose)
        
        # Check that output starts with expected string
        assert output.startswith('Fire is starting a Python REPL with the following objects:\n')
        
        # Check that categories are properly formatted
        lines = output.split('\n')
        for line in lines[1:]:  # Skip first line
            if line.strip():  # Non-empty lines
                # Should be either "Modules: ..." or "Objects: ..."
                if 'Modules:' in line or 'Objects:' in line:
                    assert ':' in line, f"Category line missing colon: {line}"


@given(st.booleans())
def test_empty_dict_output(verbose):
    """Test output when given an empty dictionary."""
    output = interact._AvailableString({}, verbose=verbose)
    
    # Should still have the header
    assert 'Fire is starting a Python REPL' in output
    
    # Should not have any category lines since dict is empty
    assert 'Modules:' not in output
    assert 'Objects:' not in output


@given(variables_dict(), st.booleans())
def test_verbose_flag_increases_output(variables, verbose):
    """Test that verbose=True never decreases the output."""
    # Add some underscore-prefixed variables to make difference visible
    test_vars = variables.copy()
    test_vars['_hidden1'] = 123
    test_vars['_hidden2'] = types.ModuleType('hidden_module')
    
    output_not_verbose = interact._AvailableString(test_vars, verbose=False)
    output_verbose = interact._AvailableString(test_vars, verbose=True)
    
    # Count mentioned variables in each output
    def count_vars(output):
        count = 0
        lines = output.split('\n')
        for line in lines:
            if ('Modules:' in line or 'Objects:' in line) and ':' in line:
                items_str = line.split(':', 1)[1].strip()
                if items_str:
                    items = items_str.split(',')
                    count += len(items)
        return count
    
    count_not_verbose = count_vars(output_not_verbose)
    count_verbose = count_vars(output_verbose)
    
    # Verbose should have at least as many items
    assert count_verbose >= count_not_verbose, f"Verbose mode shows fewer items: {count_verbose} < {count_not_verbose}"


if __name__ == '__main__':
    # Run the tests
    import pytest
    pytest.main([__file__, '-v'])