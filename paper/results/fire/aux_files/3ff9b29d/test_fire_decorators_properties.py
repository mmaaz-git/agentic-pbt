"""Property-based tests for fire.decorators module."""

import sys
import types
from hypothesis import given, strategies as st, assume
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import decorators


# Strategy for generating simple functions
@st.composite
def simple_functions(draw):
    """Generate simple test functions."""
    num_args = draw(st.integers(min_value=0, max_value=5))
    arg_names = [f"arg{i}" for i in range(num_args)]
    
    # Create a simple function dynamically
    func_code = f"def test_func({', '.join(arg_names)}): return sum([{', '.join(arg_names) if arg_names else '0'}])"
    exec_globals = {}
    exec(func_code, exec_globals)
    return exec_globals['test_func']


# Strategy for generating parse functions (callables that take a string)
@st.composite
def parse_functions(draw):
    """Generate valid parse functions."""
    parse_type = draw(st.sampled_from([int, float, str, bool]))
    return parse_type


# Property 1: GetMetadata always returns dict with ACCEPTS_POSITIONAL_ARGS
@given(simple_functions())
def test_get_metadata_invariant(func):
    """GetMetadata should always return a dict with ACCEPTS_POSITIONAL_ARGS key."""
    metadata = decorators.GetMetadata(func)
    assert isinstance(metadata, dict)
    assert decorators.ACCEPTS_POSITIONAL_ARGS in metadata
    assert isinstance(metadata[decorators.ACCEPTS_POSITIONAL_ARGS], bool)


# Property 2: GetParseFns always returns proper structure
@given(simple_functions())
def test_get_parse_fns_structure(func):
    """GetParseFns should always return dict with expected structure."""
    parse_fns = decorators.GetParseFns(func)
    assert isinstance(parse_fns, dict)
    assert 'default' in parse_fns
    assert 'positional' in parse_fns
    assert 'named' in parse_fns
    assert isinstance(parse_fns['positional'], (list, tuple))
    assert isinstance(parse_fns['named'], dict)


# Property 3: SetParseFns round-trip property
@given(
    simple_functions(),
    st.lists(parse_functions(), min_size=0, max_size=3),
    st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=st.characters(categories=['Ll'])),
        parse_functions(),
        min_size=0,
        max_size=3
    )
)
def test_set_parse_fns_round_trip(func, positional_fns, named_fns):
    """SetParseFns values should be retrievable via GetParseFns."""
    # Apply decorator
    decorated = decorators.SetParseFns(*positional_fns, **named_fns)(func)
    
    # Retrieve parse functions
    retrieved = decorators.GetParseFns(decorated)
    
    # Check round-trip
    assert retrieved['positional'] == positional_fns
    assert retrieved['named'] == named_fns


# Property 4: Function preservation - decorated function should work the same
@given(
    st.lists(st.integers(), min_size=0, max_size=5),
    st.lists(parse_functions(), min_size=0, max_size=3)
)
def test_function_preservation(args, parse_fns):
    """Decorating a function should not change its behavior when called directly."""
    # Create a simple function
    def original(*args):
        return sum(args) if args else 0
    
    # Create decorated version
    decorated = decorators.SetParseFns(*parse_fns)(original)
    
    # Both should produce same result when called directly
    assert original(*args) == decorated(*args)


# Property 5: SetParseFn with no arguments sets 'default'
@given(
    simple_functions(),
    parse_functions()
)
def test_set_parse_fn_default(func, parse_fn):
    """SetParseFn with no arguments should set the 'default' parse function."""
    decorated = decorators.SetParseFn(parse_fn)(func)
    retrieved = decorators.GetParseFns(decorated)
    assert retrieved['default'] == parse_fn


# Property 6: SetParseFn with arguments sets 'named' entries
@given(
    simple_functions(),
    parse_functions(),
    st.lists(
        st.text(min_size=1, max_size=10, alphabet=st.characters(categories=['Ll'])),
        min_size=1,
        max_size=3,
        unique=True
    )
)
def test_set_parse_fn_named(func, parse_fn, arg_names):
    """SetParseFn with arguments should set the 'named' parse functions."""
    decorated = decorators.SetParseFn(parse_fn, *arg_names)(func)
    retrieved = decorators.GetParseFns(decorated)
    
    for arg_name in arg_names:
        assert arg_name in retrieved['named']
        assert retrieved['named'][arg_name] == parse_fn


# Property 7: Metadata composition - multiple decorator applications
@given(
    simple_functions(),
    st.lists(parse_functions(), min_size=1, max_size=2),
    st.lists(
        st.text(min_size=1, max_size=5, alphabet=st.characters(categories=['Ll'])),
        min_size=1,
        max_size=2,
        unique=True
    )
)
def test_metadata_composition(func, parse_fns, arg_names):
    """Multiple decorator applications should compose predictably."""
    # Apply first decorator
    decorated = decorators.SetParseFn(parse_fns[0], arg_names[0])(func)
    
    # Apply second decorator with different argument if we have more
    if len(parse_fns) > 1 and len(arg_names) > 1:
        decorated = decorators.SetParseFn(parse_fns[1], arg_names[1])(decorated)
        
        # Both should be in the metadata
        retrieved = decorators.GetParseFns(decorated)
        assert arg_names[0] in retrieved['named']
        assert arg_names[1] in retrieved['named']
        assert retrieved['named'][arg_names[0]] == parse_fns[0]
        assert retrieved['named'][arg_names[1]] == parse_fns[1]


# Property 8: GetMetadata handles functions without metadata gracefully
@given(simple_functions())
def test_get_metadata_no_metadata(func):
    """GetMetadata should handle functions without FIRE_METADATA attribute."""
    # Ensure function has no FIRE_METADATA
    if hasattr(func, decorators.FIRE_METADATA):
        delattr(func, decorators.FIRE_METADATA)
    
    metadata = decorators.GetMetadata(func)
    assert isinstance(metadata, dict)
    assert decorators.ACCEPTS_POSITIONAL_ARGS in metadata


# Property 9: Empty SetParseFns doesn't break GetParseFns
@given(simple_functions())
def test_empty_set_parse_fns(func):
    """SetParseFns with no arguments should still create valid metadata."""
    decorated = decorators.SetParseFns()(func)
    retrieved = decorators.GetParseFns(decorated)
    
    assert isinstance(retrieved, dict)
    assert 'default' in retrieved
    assert 'positional' in retrieved
    assert 'named' in retrieved
    assert retrieved['positional'] == ()
    assert retrieved['named'] == {}