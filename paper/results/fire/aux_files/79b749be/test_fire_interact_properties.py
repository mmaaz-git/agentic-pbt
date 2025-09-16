#!/usr/bin/env python3
"""Property-based tests for fire.interact module using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import fire.interact as interact
import types
import re
from unittest import mock


@composite
def variable_dict_with_underscores(draw):
    """Generate dict with mix of underscore and non-underscore keys."""
    n_normal = draw(st.integers(min_value=0, max_value=5))
    n_underscore = draw(st.integers(min_value=1, max_value=5))
    
    normal_keys = draw(st.lists(
        st.from_regex(r'^[a-zA-Z][a-zA-Z0-9]*$', fullmatch=True),
        min_size=n_normal, max_size=n_normal, unique=True
    ))
    
    underscore_keys = draw(st.lists(
        st.from_regex(r'^_[a-zA-Z][a-zA-Z0-9_]*$', fullmatch=True),
        min_size=n_underscore, max_size=n_underscore, unique=True
    ))
    
    all_keys = normal_keys + underscore_keys
    values = draw(st.lists(
        st.one_of(st.integers(), st.text(), st.none()),
        min_size=len(all_keys), max_size=len(all_keys)
    ))
    
    return dict(zip(all_keys, values))


@given(variable_dict_with_underscores())
def test_available_string_underscore_visibility(variables):
    """Variables starting with '_' should only appear when verbose=True."""
    result_verbose_false = interact._AvailableString(variables, verbose=False)
    result_verbose_true = interact._AvailableString(variables, verbose=True)
    
    for key in variables:
        if key.startswith('_'):
            assert key not in result_verbose_false
            assert key in result_verbose_true or '-' in key or '/' in key
        elif '-' not in key and '/' not in key:
            assert key in result_verbose_false or key in result_verbose_true


@given(st.dictionaries(
    st.one_of(
        st.from_regex(r'^[a-zA-Z_][a-zA-Z0-9_]*-[a-zA-Z0-9_-]*$', fullmatch=True),
        st.from_regex(r'^[a-zA-Z_][a-zA-Z0-9_]*/[a-zA-Z0-9_/]*$', fullmatch=True)
    ),
    st.one_of(st.integers(), st.text(), st.none()),
    min_size=1
))
def test_available_string_hyphen_slash_filtering(variables):
    """Keys containing '-' or '/' should never appear in output."""
    for verbose in [False, True]:
        result = interact._AvailableString(variables, verbose=verbose)
        for key in variables:
            if '-' in key or '/' in key:
                assert key not in result


@composite
def variable_dict_with_modules(draw):
    """Generate dict with mix of modules and non-modules."""
    n_modules = draw(st.integers(min_value=0, max_value=3))
    n_other = draw(st.integers(min_value=0, max_value=5))
    
    module_keys = draw(st.lists(
        st.from_regex(r'^[a-zA-Z][a-zA-Z0-9]*$', fullmatch=True),
        min_size=n_modules, max_size=n_modules, unique=True
    ))
    
    other_keys = draw(st.lists(
        st.from_regex(r'^[a-zA-Z][a-zA-Z0-9]*$', fullmatch=True),
        min_size=n_other, max_size=n_other, unique=True
    ))
    
    all_keys = list(set(module_keys) | set(other_keys))
    
    result = {}
    for key in all_keys:
        if key in module_keys:
            result[key] = types.ModuleType(key)
        else:
            result[key] = draw(st.one_of(st.integers(), st.text(), st.none()))
    
    return result


@given(variable_dict_with_modules())
def test_available_string_module_categorization(variables):
    """Modules should be categorized as 'Modules', others as 'Objects'."""
    result = interact._AvailableString(variables, verbose=False)
    
    modules_expected = []
    objects_expected = []
    
    for key, value in variables.items():
        if not key.startswith('_') and '-' not in key and '/' not in key:
            if isinstance(value, types.ModuleType):
                modules_expected.append(key)
            else:
                objects_expected.append(key)
    
    if modules_expected:
        assert 'Modules:' in result
        for module in modules_expected:
            assert module in result
    
    if objects_expected:
        assert 'Objects:' in result
        for obj in objects_expected:
            assert obj in result


@given(st.dictionaries(
    st.from_regex(r'^[a-zA-Z][a-zA-Z0-9]*$', fullmatch=True),
    st.one_of(st.integers(), st.text(), st.none()),
    min_size=2, max_size=10
))
def test_available_string_sorting(variables):
    """Variables should be sorted alphabetically in each category."""
    result = interact._AvailableString(variables, verbose=False)
    
    lines = result.split('\n')
    for line in lines:
        if line.startswith('Objects:') or line.startswith('Modules:'):
            items_part = line.split(': ', 1)[1]
            items = [item.strip() for item in items_part.split(',')]
            assert items == sorted(items)


@given(st.dictionaries(
    st.from_regex(r'^[a-zA-Z_][a-zA-Z0-9_]*$', fullmatch=True),
    st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.none(),
        st.lists(st.integers(), max_size=5),
        st.dictionaries(st.text(), st.integers(), max_size=3)
    ),
    max_size=20
))
@settings(max_examples=50)
def test_embed_crash_resilience(variables):
    """Embed should not crash with various input types."""
    with mock.patch('fire.interact._EmbedIPython'), \
         mock.patch('fire.interact._EmbedCode'), \
         mock.patch('builtins.print'):
        try:
            interact.Embed(variables)
            interact.Embed(variables, verbose=True)
            interact.Embed(variables, verbose=False)
        except Exception as e:
            assert False, f"Embed crashed with: {e}"


@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(st.integers(), st.text(), st.none()),
    max_size=10
))
def test_available_string_structure(variables):
    """_AvailableString should always return a properly formatted string."""
    for verbose in [False, True]:
        result = interact._AvailableString(variables, verbose=verbose)
        
        assert isinstance(result, str)
        assert result.startswith('Fire is starting a Python REPL')
        assert '\n' in result
        
        visible_keys = [k for k in variables.keys() 
                       if (not k.startswith('_') or verbose) 
                       and '-' not in k and '/' not in k]
        
        if not visible_keys:
            assert 'Modules:' not in result and 'Objects:' not in result


@given(st.dictionaries(
    st.from_regex(r'^[a-zA-Z][a-zA-Z0-9]*$', fullmatch=True),
    st.none(),
    min_size=1, max_size=5
))
def test_available_string_all_none_values(variables):
    """Test behavior when all values are None."""
    result = interact._AvailableString(variables, verbose=False)
    
    assert 'Objects:' in result
    for key in variables:
        assert key in result


@composite
def dict_with_edge_case_keys(draw):
    """Generate dict with edge case keys."""
    keys = []
    
    if draw(st.booleans()):
        keys.append(draw(st.from_regex(r'^_{2,}[a-zA-Z]*$', fullmatch=True)))
    
    if draw(st.booleans()):
        keys.append(draw(st.from_regex(r'^[a-zA-Z]+_{2,}$', fullmatch=True)))
    
    if draw(st.booleans()):
        keys.append(draw(st.from_regex(r'^[a-zA-Z]+_[a-zA-Z]+$', fullmatch=True)))
    
    if draw(st.booleans()):
        keys.append('')
    
    normal_keys = draw(st.lists(
        st.from_regex(r'^[a-zA-Z][a-zA-Z0-9]*$', fullmatch=True),
        min_size=0, max_size=3, unique=True
    ))
    
    all_keys = list(set(keys + normal_keys))
    if not all_keys:
        all_keys = ['default_key']
    
    values = draw(st.lists(
        st.one_of(st.integers(), st.text(), st.none()),
        min_size=len(all_keys), max_size=len(all_keys)
    ))
    
    return dict(zip(all_keys, values))


@given(dict_with_edge_case_keys())
def test_available_string_edge_case_keys(variables):
    """Test with edge case keys like multiple underscores, empty string."""
    for verbose in [False, True]:
        try:
            result = interact._AvailableString(variables, verbose=verbose)
            assert isinstance(result, str)
            
            for key in variables:
                if key == '':
                    assert key not in result
                elif key.startswith('_') and not verbose:
                    assert key not in result
                elif '-' in key or '/' in key:
                    assert key not in result
        except Exception as e:
            assert False, f"Failed with edge case keys: {e}"


@given(st.integers(min_value=0, max_value=100))
def test_available_string_large_dict(n):
    """Test with large dictionaries."""
    variables = {f'var{i}': i for i in range(n)}
    
    for verbose in [False, True]:
        result = interact._AvailableString(variables, verbose=verbose)
        assert isinstance(result, str)
        
        if n > 0:
            assert 'Objects:' in result
            items_line = [line for line in result.split('\n') if line.startswith('Objects:')][0]
            items = items_line.split(': ')[1].split(', ')
            assert len(items) == n
            assert items == sorted(items)


@given(st.dictionaries(
    st.from_regex(r'^[a-zA-Z][a-zA-Z0-9]*$', fullmatch=True),
    st.sampled_from([
        float('inf'), float('-inf'), float('nan'),
        complex(1, 2), lambda x: x, type, object()
    ]),
    min_size=1, max_size=5
))
def test_available_string_special_values(variables):
    """Test with special Python values."""
    for verbose in [False, True]:
        result = interact._AvailableString(variables, verbose=verbose)
        assert isinstance(result, str)
        assert 'Objects:' in result
        
        for key in variables:
            assert key in result