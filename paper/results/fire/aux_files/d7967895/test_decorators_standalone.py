#!/usr/bin/env python3
"""Standalone property-based tests for fire.decorators module."""

import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import fire.decorators as decorators


# Strategy for generating valid Python function names
import keyword
valid_fn_names = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_',
    min_size=1,
    max_size=20
).filter(lambda s: not s[0].isdigit() and not keyword.iskeyword(s))

# Strategy for generating simple functions
@st.composite
def simple_functions(draw):
    name = draw(valid_fn_names)
    num_args = draw(st.integers(min_value=0, max_value=5))
    arg_names = draw(st.lists(valid_fn_names, min_size=num_args, max_size=num_args, unique=True))
    
    # Create function dynamically
    args_str = ', '.join(arg_names) if arg_names else ''
    func_str = f"def {name}({args_str}): return None"
    local_dict = {}
    exec(func_str, {}, local_dict)
    return local_dict[name]


# Property 1: GetMetadata always returns a dictionary with ACCEPTS_POSITIONAL_ARGS
@given(simple_functions())
@settings(max_examples=100)
def test_metadata_always_has_accepts_positional_args(func):
    metadata = decorators.GetMetadata(func)
    assert isinstance(metadata, dict)
    assert decorators.ACCEPTS_POSITIONAL_ARGS in metadata
    assert isinstance(metadata[decorators.ACCEPTS_POSITIONAL_ARGS], bool)
    print(".", end="", flush=True)


# Property 2: GetParseFns always returns expected structure
@given(simple_functions())
@settings(max_examples=100)
def test_parse_fns_structure(func):
    parse_fns = decorators.GetParseFns(func)
    assert isinstance(parse_fns, dict)
    assert 'default' in parse_fns
    assert 'positional' in parse_fns
    assert 'named' in parse_fns
    assert isinstance(parse_fns['positional'], (list, tuple))
    assert isinstance(parse_fns['named'], dict)
    print(".", end="", flush=True)


# Property 3: Decorator round-trip preserves parse functions
@given(simple_functions(), valid_fn_names)
@settings(max_examples=100)
def test_set_parse_fn_roundtrip(func, arg_name):
    # Apply SetParseFn decorator with a parse function
    parse_fn = str  # Use str as a simple parse function
    decorated = decorators.SetParseFn(parse_fn, arg_name)(func)
    
    # Retrieve parse functions
    parse_fns = decorators.GetParseFns(decorated)
    
    # Check that the parse function was stored correctly
    assert arg_name in parse_fns['named']
    assert parse_fns['named'][arg_name] is parse_fn
    print(".", end="", flush=True)


# Property 4: SetParseFn without arguments sets default
@given(simple_functions())
@settings(max_examples=100)
def test_set_parse_fn_default(func):
    parse_fn = int
    decorated = decorators.SetParseFn(parse_fn)(func)
    
    parse_fns = decorators.GetParseFns(decorated)
    assert parse_fns['default'] is parse_fn
    print(".", end="", flush=True)


# Property 5: Multiple SetParseFn applications update correctly
@given(simple_functions(), st.lists(valid_fn_names, min_size=2, max_size=5, unique=True))
@settings(max_examples=100)
def test_multiple_set_parse_fn_applications(func, arg_names):
    decorated = func
    parse_fns_map = {}
    
    # Apply multiple SetParseFn decorators
    for i, arg_name in enumerate(arg_names):
        parse_fn = [str, int, float, list, dict][i % 5]
        parse_fns_map[arg_name] = parse_fn
        decorated = decorators.SetParseFn(parse_fn, arg_name)(decorated)
    
    # Check all parse functions are preserved
    result_parse_fns = decorators.GetParseFns(decorated)
    for arg_name, expected_fn in parse_fns_map.items():
        assert arg_name in result_parse_fns['named']
        assert result_parse_fns['named'][arg_name] is expected_fn
    print(".", end="", flush=True)


# Property 6: SetParseFns with positional and named arguments
@given(
    simple_functions(),
    st.lists(st.sampled_from([str, int, float, bool]), min_size=0, max_size=3),
    st.dictionaries(valid_fn_names, st.sampled_from([str, int, float, bool]), max_size=3)
)
@settings(max_examples=100)
def test_set_parse_fns_positional_and_named(func, positional_fns, named_fns):
    decorated = decorators.SetParseFns(*positional_fns, **named_fns)(func)
    
    parse_fns = decorators.GetParseFns(decorated)
    
    # Check positional functions
    assert parse_fns['positional'] == positional_fns
    
    # Check named functions
    for name, fn in named_fns.items():
        assert name in parse_fns['named']
        assert parse_fns['named'][name] is fn
    print(".", end="", flush=True)


# Property 7: Metadata survives multiple operations
@given(simple_functions(), st.data())
@settings(max_examples=100)
def test_metadata_persistence(func, data):
    # Apply a series of operations
    decorated = func
    
    # First decoration
    parse_fn1 = str
    arg1 = data.draw(valid_fn_names)
    decorated = decorators.SetParseFn(parse_fn1, arg1)(decorated)
    
    # Check metadata still has required keys
    metadata1 = decorators.GetMetadata(decorated)
    assert decorators.ACCEPTS_POSITIONAL_ARGS in metadata1
    
    # Second decoration
    parse_fn2 = int
    decorated = decorators.SetParseFn(parse_fn2)(decorated)  # Set default
    
    # Check metadata integrity
    metadata2 = decorators.GetMetadata(decorated)
    assert decorators.ACCEPTS_POSITIONAL_ARGS in metadata2
    
    # Verify both parse functions are preserved
    parse_fns = decorators.GetParseFns(decorated)
    assert parse_fns['default'] is parse_fn2
    assert arg1 in parse_fns['named']
    assert parse_fns['named'][arg1] is parse_fn1
    print(".", end="", flush=True)


# Property 8: GetMetadata handles objects without metadata gracefully
@given(st.sampled_from([None, 42, "string", [], {}, object(), lambda x: x]))
@settings(max_examples=100)
def test_get_metadata_robustness(obj):
    # GetMetadata should handle any object gracefully
    metadata = decorators.GetMetadata(obj)
    assert isinstance(metadata, dict)
    assert decorators.ACCEPTS_POSITIONAL_ARGS in metadata
    print(".", end="", flush=True)


# Property 9: Overwriting parse functions works correctly
@given(simple_functions(), valid_fn_names)
@settings(max_examples=100)
def test_overwriting_parse_functions(func, arg_name):
    # Set initial parse function
    decorated = decorators.SetParseFn(str, arg_name)(func)
    parse_fns1 = decorators.GetParseFns(decorated)
    assert parse_fns1['named'][arg_name] is str
    
    # Overwrite with new parse function
    decorated = decorators.SetParseFn(int, arg_name)(decorated)
    parse_fns2 = decorators.GetParseFns(decorated)
    assert parse_fns2['named'][arg_name] is int
    
    # The old parse function should be completely replaced
    assert parse_fns2['named'][arg_name] is not str
    print(".", end="", flush=True)


# Property 10: Empty SetParseFns call preserves structure
@given(simple_functions())
@settings(max_examples=100)
def test_empty_set_parse_fns(func):
    decorated = decorators.SetParseFns()(func)
    parse_fns = decorators.GetParseFns(decorated)
    
    # Should have the expected structure even with no arguments
    assert 'default' in parse_fns
    assert 'positional' in parse_fns
    assert 'named' in parse_fns
    assert parse_fns['positional'] == ()
    assert isinstance(parse_fns['named'], dict)
    print(".", end="", flush=True)


def run_all_tests():
    """Run all property-based tests."""
    print("Running property-based tests for fire.decorators...")
    print("\nTest 1: Metadata preservation")
    test_metadata_always_has_accepts_positional_args()
    
    print("\n\nTest 2: Parse functions structure")
    test_parse_fns_structure()
    
    print("\n\nTest 3: Decorator round-trip")
    test_set_parse_fn_roundtrip()
    
    print("\n\nTest 4: SetParseFn default")
    test_set_parse_fn_default()
    
    print("\n\nTest 5: Multiple SetParseFn applications")
    test_multiple_set_parse_fn_applications()
    
    print("\n\nTest 6: SetParseFns positional and named")
    test_set_parse_fns_positional_and_named()
    
    print("\n\nTest 7: Metadata persistence")
    test_metadata_persistence()
    
    print("\n\nTest 8: GetMetadata robustness")
    test_get_metadata_robustness()
    
    print("\n\nTest 9: Overwriting parse functions")
    test_overwriting_parse_functions()
    
    print("\n\nTest 10: Empty SetParseFns")
    test_empty_set_parse_fns()
    
    print("\n\nAll tests passed!")


if __name__ == '__main__':
    run_all_tests()