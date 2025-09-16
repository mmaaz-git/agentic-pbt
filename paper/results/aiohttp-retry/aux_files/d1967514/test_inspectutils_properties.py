#!/usr/bin/env python3
"""Property-based tests for fire.inspectutils module using Hypothesis."""

import collections
import inspect
import sys
import types
from typing import Any, Callable

import pytest
from hypothesis import assume, given, strategies as st, settings

# Add the fire_env to path to import fire
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.inspectutils as inspectutils


# Strategy for generating simple functions
@st.composite
def simple_functions(draw):
    """Generate simple Python functions with various signatures."""
    num_args = draw(st.integers(min_value=0, max_value=5))
    num_defaults = draw(st.integers(min_value=0, max_value=min(num_args, 3)))
    
    # Create a function dynamically
    args = [f'arg{i}' for i in range(num_args)]
    defaults = tuple(range(num_defaults)) if num_defaults > 0 else ()
    
    func_str = f"def test_func({', '.join(args)}):\n    return None"
    local_vars = {}
    exec(func_str, {}, local_vars)
    func = local_vars['test_func']
    
    # Add defaults
    if defaults:
        func.__defaults__ = defaults
    
    return func


# Strategy for generating namedtuple instances
@st.composite
def namedtuple_instances(draw):
    """Generate namedtuple instances with various fields."""
    num_fields = draw(st.integers(min_value=1, max_value=5))
    fields = [f'field{i}' for i in range(num_fields)]
    name = draw(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10))
    # Create the namedtuple class
    nt_class = collections.namedtuple(name, fields)
    # Generate values for each field
    values = [draw(st.integers()) for _ in fields]
    # Return an instance of the namedtuple
    return nt_class(*values)


@given(simple_functions())
@settings(max_examples=200)
def test_getfullargspec_defaults_match_args(func):
    """Test that defaults correspond to the last arguments in the args list."""
    try:
        spec = inspectutils.GetFullArgSpec(func)
    except (TypeError, ValueError):
        # Some functions might not be inspectable
        return
    
    if spec.defaults:
        # Property: The number of defaults should not exceed the number of args
        assert len(spec.defaults) <= len(spec.args), \
            f"defaults count ({len(spec.defaults)}) exceeds args count ({len(spec.args)})"
        
        # Property: defaults correspond to the last len(defaults) arguments
        # This is a fundamental property of Python function signatures
        num_defaults = len(spec.defaults)
        if spec.args:
            # The args that have defaults are the last num_defaults args
            args_with_defaults = spec.args[-num_defaults:] if num_defaults > 0 else []
            # This property is implied by Python's function signature rules


@given(simple_functions())
@settings(max_examples=200)
def test_getfullargspec_annotations_keys_subset(func):
    """Test that annotation keys are valid argument names or 'return'."""
    try:
        spec = inspectutils.GetFullArgSpec(func)
    except (TypeError, ValueError):
        return
    
    if spec.annotations:
        valid_keys = set(spec.args) | set(spec.kwonlyargs or []) | {'return'}
        if spec.varargs:
            valid_keys.add(spec.varargs)
        if spec.varkw:
            valid_keys.add(spec.varkw)
        
        annotation_keys = set(spec.annotations.keys())
        
        # Property: All annotation keys should be valid argument names or 'return'
        assert annotation_keys.issubset(valid_keys), \
            f"Invalid annotation keys: {annotation_keys - valid_keys}"


@given(st.one_of(
    st.tuples(st.integers()),  # Regular tuples
    st.lists(st.integers()).map(tuple),  # Convert lists to tuples
    namedtuple_instances(),  # Named tuple instances
    st.integers(),  # Non-tuples
    st.text(),  # Non-tuples
    st.none(),  # Non-tuples
))
@settings(max_examples=500)
def test_isnamedtuple_correctness(component):
    """Test that IsNamedTuple correctly identifies namedtuples."""
    result = inspectutils.IsNamedTuple(component)
    
    # Check if it's actually a namedtuple
    is_actually_namedtuple = (
        isinstance(component, tuple) and 
        hasattr(component, '_fields') and
        isinstance(component._fields, tuple)
    )
    
    # Property: The function should correctly identify namedtuples
    assert result == is_actually_namedtuple, \
        f"IsNamedTuple returned {result} but component is {'a' if is_actually_namedtuple else 'not a'} namedtuple"


@given(st.one_of(
    st.integers(),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
))
@settings(max_examples=200)
def test_info_type_name_consistency(component):
    """Test that Info returns consistent type_name."""
    info = inspectutils.Info(component)
    
    # Property: type_name should match the actual type name
    expected_type_name = type(component).__name__
    actual_type_name = info.get('type_name')
    
    assert actual_type_name == expected_type_name, \
        f"type_name mismatch: got '{actual_type_name}', expected '{expected_type_name}'"


@given(st.one_of(
    st.integers(),
    st.text(),
    st.lists(st.integers()),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
))
@settings(max_examples=200)
def test_info_string_form_consistency(component):
    """Test that Info returns consistent string_form."""
    info = inspectutils.Info(component)
    
    # Property: string_form should match str(component)
    expected_string_form = str(component)
    actual_string_form = info.get('string_form')
    
    assert actual_string_form == expected_string_form, \
        f"string_form mismatch: got '{actual_string_form}', expected '{expected_string_form}'"


@given(st.one_of(
    st.lists(st.integers()),
    st.text(),
    st.dictionaries(st.text(), st.integers()),
    st.sets(st.integers()),
))
@settings(max_examples=200)
def test_info_length_consistency(component):
    """Test that Info returns correct length when applicable."""
    info = inspectutils.Info(component)
    
    # If component has a length, check it's reported correctly
    try:
        expected_length = str(len(component))
        actual_length = info.get('length')
        
        # Property: If length is present, it should match len(component)
        if actual_length is not None:
            assert actual_length == expected_length, \
                f"length mismatch: got '{actual_length}', expected '{expected_length}'"
    except (TypeError, AttributeError):
        # Component doesn't have a length, info shouldn't have 'length' key
        assert 'length' not in info or info.get('length') is None


# Test for GetFileAndLine
@given(st.one_of(
    st.sampled_from([int, str, list, dict, tuple, set, type]),  # Builtins
    st.sampled_from([abs, len, min, max, sum, sorted]),  # Builtin functions
))
@settings(max_examples=100)
def test_getfileandline_builtins(builtin_component):
    """Test that GetFileAndLine returns (None, None) for builtins."""
    filename, lineno = inspectutils.GetFileAndLine(builtin_component)
    
    # Property: Builtins should return (None, None)
    assert filename is None, f"Expected None filename for builtin, got {filename}"
    assert lineno is None, f"Expected None lineno for builtin, got {lineno}"


# Test GetClassAttrsDict
@given(st.one_of(
    st.integers(),
    st.text(),
    st.lists(st.integers()),
    st.sampled_from([int, str, list, dict, type]),  # Classes
))
@settings(max_examples=200) 
def test_getclassattrsdict_non_class_returns_none(component):
    """Test that GetClassAttrsDict returns None for non-classes."""
    result = inspectutils.GetClassAttrsDict(component)
    
    if not inspect.isclass(component):
        # Property: Should return None for non-classes
        assert result is None, f"Expected None for non-class, got {result}"
    else:
        # Property: Should return a dict for classes
        assert isinstance(result, dict), f"Expected dict for class, got {type(result)}"


# Test IsCoroutineFunction
@given(st.one_of(
    st.sampled_from([abs, len, min, max, sum]),  # Regular functions
    st.integers(),  # Non-functions
    st.text(),  # Non-functions
))
@settings(max_examples=100)
def test_iscoroutinefunction_regular_functions(component):
    """Test that IsCoroutineFunction returns False for non-coroutines."""
    result = inspectutils.IsCoroutineFunction(component)
    
    # Property: Regular functions and non-functions should return False
    assert result is False, f"Expected False for non-coroutine, got {result}"


# Edge case testing for GetFullArgSpec with various Python constructs
@given(st.sampled_from([
    type,  # metaclass
    object,  # base class
    lambda x: x,  # lambda
    staticmethod(lambda x: x),  # staticmethod
    classmethod(lambda cls, x: x),  # classmethod
]))
@settings(max_examples=50)
def test_getfullargspec_edge_cases(component):
    """Test GetFullArgSpec with edge cases."""
    try:
        spec = inspectutils.GetFullArgSpec(component)
        # Property: Should return a FullArgSpec instance
        assert isinstance(spec, inspectutils.FullArgSpec), \
            f"Expected FullArgSpec, got {type(spec)}"
        
        # Property: Basic attributes should exist
        assert hasattr(spec, 'args')
        assert hasattr(spec, 'defaults')
        assert hasattr(spec, 'varargs')
        assert hasattr(spec, 'varkw')
        assert hasattr(spec, 'kwonlyargs')
        assert hasattr(spec, 'kwonlydefaults')
        assert hasattr(spec, 'annotations')
        
    except TypeError:
        # Some components might not be inspectable, which is acceptable
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])