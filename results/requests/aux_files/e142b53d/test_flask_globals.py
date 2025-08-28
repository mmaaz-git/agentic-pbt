"""Property-based tests for flask.globals module."""

import flask
from flask import g, current_app
from hypothesis import given, strategies as st, assume
import string
import pytest


# Strategy for valid Python attribute names
valid_attr_names = st.text(
    alphabet=string.ascii_letters + string.digits + "_",
    min_size=1,
    max_size=100
).filter(lambda s: s[0] not in string.digits and not s.startswith('_'))

# Strategy for various Python values
python_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(max_size=10), st.integers(), max_size=5)
)


@given(valid_attr_names, python_values, valid_attr_names, python_values)
def test_context_isolation(name1, value1, name2, value2):
    """Test that values in one app context don't leak to another."""
    assume(name1 != name2)  # Make sure we're testing different attributes
    
    app1 = flask.Flask(__name__)
    app2 = flask.Flask(__name__)
    
    # Set value in first app's context
    with app1.app_context():
        setattr(g, name1, value1)
        assert getattr(g, name1) == value1
    
    # Check second app's context is isolated
    with app2.app_context():
        # name1 should not exist in this context
        assert not hasattr(g, name1)
        
        # Set different value in second context
        setattr(g, name2, value2)
        assert getattr(g, name2) == value2
    
    # New context for app1 - should be fresh (contexts don't persist)
    with app1.app_context():
        # Each context entry is fresh, so name1 shouldn't exist
        assert not hasattr(g, name1)
        assert not hasattr(g, name2)


@given(valid_attr_names, python_values)
def test_attribute_round_trip(name, value):
    """Test that setting and getting attributes on g works correctly."""
    app = flask.Flask(__name__)
    
    with app.app_context():
        # Test initial state
        assert not hasattr(g, name)
        
        # Set and get
        setattr(g, name, value)
        assert hasattr(g, name)
        retrieved = getattr(g, name)
        assert retrieved == value
        
        # For mutable objects, check it's the same object
        if isinstance(value, (list, dict)):
            assert retrieved is value
        
        # Test deletion
        delattr(g, name)
        assert not hasattr(g, name)
        
        # Should raise AttributeError when accessing deleted attribute
        with pytest.raises(AttributeError):
            getattr(g, name)


@given(st.lists(st.tuples(valid_attr_names, python_values), min_size=1, max_size=10))
def test_multiple_attributes(attr_pairs):
    """Test that g can handle multiple attributes correctly."""
    app = flask.Flask(__name__)
    
    # Remove duplicates by keeping only first occurrence of each name
    seen = set()
    unique_pairs = []
    for name, value in attr_pairs:
        if name not in seen:
            seen.add(name)
            unique_pairs.append((name, value))
    
    with app.app_context():
        # Set all attributes
        for name, value in unique_pairs:
            setattr(g, name, value)
        
        # Verify all attributes
        for name, value in unique_pairs:
            assert hasattr(g, name)
            assert getattr(g, name) == value
        
        # Delete all and verify
        for name, _ in unique_pairs:
            delattr(g, name)
            assert not hasattr(g, name)


@given(valid_attr_names, python_values)
def test_nested_contexts(name, value):
    """Test that nested app contexts behave correctly."""
    app = flask.Flask(__name__)
    
    with app.app_context():
        # Outer context
        outer_value = f"outer_{value}"
        setattr(g, name, outer_value)
        assert getattr(g, name) == outer_value
        
        with app.app_context():
            # Inner context - should be a fresh context
            assert not hasattr(g, name)
            
            # Set different value in inner context
            inner_value = f"inner_{value}"
            setattr(g, name, inner_value)
            assert getattr(g, name) == inner_value
        
        # Back in outer context - should still have outer value
        assert getattr(g, name) == outer_value


@given(valid_attr_names)
def test_deletion_idempotence(name):
    """Test that deleting non-existent attributes raises AttributeError."""
    app = flask.Flask(__name__)
    
    with app.app_context():
        # First deletion should raise AttributeError
        with pytest.raises(AttributeError):
            delattr(g, name)
        
        # Set and delete
        setattr(g, name, "test")
        delattr(g, name)
        
        # Second deletion should also raise AttributeError
        with pytest.raises(AttributeError):
            delattr(g, name)


@given(valid_attr_names, python_values)
def test_current_app_consistency(name, value):
    """Test that current_app proxy works consistently within context."""
    app = flask.Flask(__name__)
    
    # Set some config on the app
    app.config[name] = value
    
    with app.app_context():
        # current_app should proxy to the actual app
        assert current_app.config[name] == value
        assert current_app.name == app.name
        
        # Modifications through proxy should affect the actual app
        new_value = f"modified_{value}"
        current_app.config[f"{name}_new"] = new_value
        assert app.config[f"{name}_new"] == new_value


@given(st.integers(min_value=1, max_value=5))
def test_multiple_sequential_contexts(num_contexts):
    """Test that sequential contexts don't interfere with each other."""
    apps = [flask.Flask(f"app_{i}") for i in range(num_contexts)]
    
    for i, app in enumerate(apps):
        with app.app_context():
            # Each context should start fresh
            assert not hasattr(g, 'test_value')
            
            # Set a unique value
            g.test_value = f"context_{i}"
            assert g.test_value == f"context_{i}"
            
            # Verify app identity
            assert current_app.name == f"app_{i}"
    
    # Verify contexts are truly isolated by checking again
    for i, app in enumerate(apps):
        with app.app_context():
            # Should be fresh again
            assert not hasattr(g, 'test_value')


@given(valid_attr_names, python_values)
def test_context_persistence_within_same_context(name, value):
    """Test that values persist within the same context entry."""
    app = flask.Flask(__name__)
    
    with app.app_context() as ctx:
        # Set value
        setattr(g, name, value)
        
        # Value should persist within the same context
        assert hasattr(g, name)
        assert getattr(g, name) == value
        
        # Modify value
        new_value = f"modified_{value}"
        setattr(g, name, new_value)
        assert getattr(g, name) == new_value
        
        # Push the same context again (simulating nested push)
        ctx.push()
        try:
            # Should still have the value
            assert hasattr(g, name)
            assert getattr(g, name) == new_value
        finally:
            ctx.pop()


@given(st.text(min_size=0, max_size=1000))
def test_special_attribute_names(name):
    """Test that special Python attribute names are handled correctly."""
    # Skip invalid Python identifiers
    if not name or not name.replace('_', 'a').isidentifier() or name.startswith('__'):
        return
    
    app = flask.Flask(__name__)
    
    with app.app_context():
        # Test special method names don't cause issues
        try:
            setattr(g, name, "test_value")
            assert getattr(g, name) == "test_value"
            delattr(g, name)
        except (AttributeError, TypeError):
            # Some names might be reserved
            pass


@given(st.lists(st.tuples(valid_attr_names, python_values), min_size=0, max_size=100))
def test_large_number_of_attributes(attr_pairs):
    """Test that g can handle a large number of attributes."""
    app = flask.Flask(__name__)
    
    # Remove duplicates
    seen = set()
    unique_pairs = []
    for name, value in attr_pairs:
        if name not in seen:
            seen.add(name)
            unique_pairs.append((name, value))
    
    with app.app_context():
        # Set all attributes
        for name, value in unique_pairs:
            setattr(g, name, value)
        
        # Verify all attributes
        for name, value in unique_pairs:
            assert getattr(g, name) == value
        
        # Check attribute count
        actual_attrs = {k: v for k, v in g.__dict__.items() if not k.startswith('_')}
        assert len(actual_attrs) == len(unique_pairs)


@given(valid_attr_names)
def test_proxy_error_messages(name):
    """Test that proxy error messages are consistent and informative."""
    from flask import g, current_app
    
    # Test accessing g outside context
    try:
        setattr(g, name, "value")
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "Working outside of application context" in str(e)
        assert "app.app_context()" in str(e)
    
    # Test accessing current_app outside context
    try:
        _ = current_app.name
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "Working outside of application context" in str(e)


@given(valid_attr_names, python_values)
def test_getattr_default_behavior(name, value):
    """Test that getattr with default works correctly on g."""
    app = flask.Flask(__name__)
    
    with app.app_context():
        # Test default value when attribute doesn't exist
        default = "default_value"
        result = getattr(g, name, default)
        assert result == default
        
        # Set attribute and test again
        setattr(g, name, value)
        result = getattr(g, name, default)
        assert result == value
        
        # Delete and test default again
        delattr(g, name)
        result = getattr(g, name, default)
        assert result == default


@given(st.integers(min_value=0, max_value=10))
def test_repeated_push_pop_context(num_pushes):
    """Test that repeated push/pop of contexts works correctly."""
    app = flask.Flask(__name__)
    
    with app.app_context() as ctx:
        # Set initial value
        g.base_value = "base"
        
        # Push multiple times
        for i in range(num_pushes):
            ctx.push()
            # Each push should maintain the value
            assert g.base_value == "base"
            g.base_value = f"level_{i}"
        
        # Pop multiple times
        for i in range(num_pushes):
            ctx.pop()
        
        # Should still have access to g in the original context
        assert hasattr(g, 'base_value')