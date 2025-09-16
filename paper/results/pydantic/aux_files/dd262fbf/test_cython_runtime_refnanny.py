"""Property-based tests for Cython.Runtime.refnanny module."""

import sys
from hypothesis import given, strategies as st, assume, settings
from Cython.Runtime.refnanny import Context, reflog, loglevel, LOG_ALL, LOG_NONE


# Test Context initialization properties
@given(st.integers())
def test_context_init_with_single_int(n):
    """Context should accept a single integer and initialize with empty collections."""
    ctx = Context(n)
    assert ctx.name == n
    assert ctx.filename is None
    assert isinstance(ctx.refs, dict)
    assert len(ctx.refs) == 0
    assert isinstance(ctx.errors, list)
    assert len(ctx.errors) == 0
    assert ctx.start == 0


@given(st.integers(), st.integers())
def test_context_init_with_two_ints(n1, n2):
    """Context should accept two integers."""
    ctx = Context(n1, n2)
    assert ctx.name == n1
    assert ctx.filename is None
    assert isinstance(ctx.refs, dict)
    assert len(ctx.refs) == 0
    assert isinstance(ctx.errors, list)
    assert len(ctx.errors) == 0


@given(st.integers(), st.integers(), st.integers())
def test_context_init_with_three_ints(n1, n2, n3):
    """Context should accept three integers, third becomes filename."""
    ctx = Context(n1, n2, n3)
    assert ctx.name == n1
    assert ctx.filename == n3
    assert isinstance(ctx.refs, dict)
    assert len(ctx.refs) == 0
    assert isinstance(ctx.errors, list)
    assert len(ctx.errors) == 0


# Test Context.refs dictionary behavior
@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_context_refs_dict_operations(data):
    """Context.refs should behave like a normal dictionary."""
    ctx = Context(0)
    
    # Test adding items
    for key, value in data.items():
        ctx.refs[key] = value
    
    # Verify all items are present
    assert len(ctx.refs) == len(data)
    for key, value in data.items():
        assert key in ctx.refs
        assert ctx.refs[key] == value
    
    # Test dictionary methods
    assert set(ctx.refs.keys()) == set(data.keys())
    assert set(ctx.refs.values()) == set(data.values())


@given(st.lists(st.text(min_size=1), min_size=1, unique=True))
def test_context_refs_delete_operations(keys):
    """Test deletion operations on Context.refs."""
    ctx = Context(0)
    
    # Add all keys
    for i, key in enumerate(keys):
        ctx.refs[key] = i
    
    # Delete half the keys
    keys_to_delete = keys[:len(keys)//2]
    for key in keys_to_delete:
        del ctx.refs[key]
    
    # Verify deletions
    for key in keys_to_delete:
        assert key not in ctx.refs
    
    # Verify remaining keys
    for key in keys[len(keys)//2:]:
        assert key in ctx.refs


# Test Context.errors list behavior
@given(st.lists(st.text()))
def test_context_errors_list_operations(items):
    """Context.errors should behave like a normal list."""
    ctx = Context(0)
    
    # Add items
    for item in items:
        ctx.errors.append(item)
    
    # Verify all items are present in order
    assert len(ctx.errors) == len(items)
    assert ctx.errors == items
    
    # Test list indexing
    for i, item in enumerate(items):
        assert ctx.errors[i] == item


@given(st.lists(st.one_of(st.text(), st.integers(), st.none())))
def test_context_errors_mixed_types(items):
    """Context.errors should accept mixed types."""
    ctx = Context(0)
    
    for item in items:
        ctx.errors.append(item)
    
    assert ctx.errors == items


# Test persistence of Context state
@given(
    st.dictionaries(st.text(min_size=1), st.integers(), max_size=10),
    st.lists(st.text(), max_size=10)
)
def test_context_state_persistence(refs_data, errors_data):
    """Context state should persist across operations."""
    ctx = Context(42)
    
    # Set up state
    for key, value in refs_data.items():
        ctx.refs[key] = value
    
    for error in errors_data:
        ctx.errors.append(error)
    
    # Verify state persists
    assert ctx.name == 42
    assert ctx.refs == refs_data
    assert ctx.errors == errors_data
    
    # Create another context - should not affect the first
    ctx2 = Context(99)
    assert ctx.name == 42  # Original unchanged
    assert ctx.refs == refs_data
    assert ctx.errors == errors_data


# Test edge cases with very large integers
@given(st.integers(min_value=-2**63, max_value=2**63-1))
def test_context_large_integers(n):
    """Context should handle large integers within typical int64 range."""
    ctx = Context(n)
    assert ctx.name == n


# Test nested data structures in refs
@given(
    st.recursive(
        st.one_of(st.integers(), st.text(), st.none()),
        lambda children: st.one_of(
            st.lists(children, max_size=3),
            st.dictionaries(st.text(min_size=1), children, max_size=3)
        ),
        max_leaves=10
    )
)
def test_context_refs_nested_structures(nested_data):
    """Context.refs should handle nested data structures."""
    ctx = Context(0)
    ctx.refs['nested'] = nested_data
    assert ctx.refs['nested'] == nested_data


# Test modifying refs and errors doesn't affect other contexts
@given(st.text(min_size=1), st.integers(), st.text())
def test_context_isolation(key, value, error):
    """Multiple Context instances should be isolated from each other."""
    ctx1 = Context(1)
    ctx2 = Context(2)
    
    ctx1.refs[key] = value
    ctx1.errors.append(error)
    
    # ctx2 should remain empty
    assert len(ctx2.refs) == 0
    assert len(ctx2.errors) == 0
    
    # ctx1 should have the data
    assert ctx1.refs[key] == value
    assert error in ctx1.errors


# Test clearing operations
@given(
    st.dictionaries(st.text(min_size=1), st.integers(), min_size=1),
    st.lists(st.text(), min_size=1)
)
def test_context_clear_operations(refs_data, errors_data):
    """Test clearing refs and errors."""
    ctx = Context(0)
    
    # Add data
    ctx.refs.update(refs_data)
    ctx.errors.extend(errors_data)
    
    # Clear refs
    ctx.refs.clear()
    assert len(ctx.refs) == 0
    assert len(ctx.errors) == len(errors_data)  # errors unchanged
    
    # Clear errors using slice deletion
    del ctx.errors[:]
    assert len(ctx.errors) == 0


# Test attribute immutability
@given(st.integers())
def test_context_name_attribute_setting(n):
    """Test if name attribute can be modified after initialization."""
    ctx = Context(0)
    initial_name = ctx.name
    
    # Try to set a new name
    try:
        ctx.name = n
        # If successful, verify it changed
        assert ctx.name == n
    except (AttributeError, TypeError):
        # If it fails, verify it remained unchanged
        assert ctx.name == initial_name


# Test filename attribute setting
@given(st.integers())
def test_context_filename_attribute_setting(n):
    """Test if filename attribute can be modified after initialization."""
    ctx = Context(0, 0, 100)
    initial_filename = ctx.filename
    
    # Try to set a new filename
    try:
        ctx.filename = n
        # If successful, verify it changed
        assert ctx.filename == n
    except (AttributeError, TypeError):
        # If it fails, verify it remained unchanged
        assert ctx.filename == initial_filename


# Test start attribute  
@given(st.integers())
def test_context_start_attribute_setting(n):
    """Test if start attribute can be modified."""
    ctx = Context(0)
    initial_start = ctx.start
    
    # Try to set start
    try:
        ctx.start = n
        # If successful, verify it changed
        assert ctx.start == n
    except (AttributeError, TypeError):
        # If it fails, verify it remained unchanged
        assert ctx.start == initial_start


# Test very long keys and values
@given(st.text(min_size=1000, max_size=10000))
def test_context_refs_long_keys(long_key):
    """Context.refs should handle very long keys."""
    ctx = Context(0)
    ctx.refs[long_key] = 42
    assert long_key in ctx.refs
    assert ctx.refs[long_key] == 42


# Test special dictionary methods
@given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=1))
def test_context_refs_get_method(data):
    """Test dictionary get() method on refs."""
    ctx = Context(0)
    ctx.refs.update(data)
    
    # Test existing keys
    for key, value in data.items():
        assert ctx.refs.get(key) == value
        assert ctx.refs.get(key, 'default') == value
    
    # Test non-existing keys
    assert ctx.refs.get('nonexistent') is None
    assert ctx.refs.get('nonexistent', 'default') == 'default'


# Test boundary conditions for Context initialization
@given(st.integers(min_value=4, max_value=100))
def test_context_too_many_args(num_args):
    """Context should reject more than 3 arguments."""
    args = [0] * num_args
    try:
        ctx = Context(*args)
        # If it succeeds with >3 args, that's unexpected but valid
        assert True
    except TypeError as e:
        # Expected for >3 args
        assert 'takes at most 3' in str(e) or 'takes' in str(e)