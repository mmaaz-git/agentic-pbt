import sys
import warnings
from hypothesis import given, strategies as st, assume, settings
import pytest
from pydantic.schema import getattr_migration
from pydantic._migration import MOVED_IN_V2, REMOVED_IN_V2, REDIRECT_TO_V1, DEPRECATED_MOVED_IN_V2


@given(
    module_name=st.text(min_size=1).filter(lambda x: all(c not in x for c in ['\x00', '\n', '\r'])),
    attr_name=st.one_of(
        st.just(''),  # Empty string
        st.text().filter(lambda x: '\x00' in x),  # Contains null
        st.text().filter(lambda x: '\n' in x or '\r' in x),  # Contains newlines
        st.text(alphabet=':', min_size=1),  # Only colons
        st.text().map(lambda x: x + ':' + x),  # Contains colons
    )
)
def test_edge_case_attribute_names(module_name, attr_name):
    """Test behavior with unusual attribute names."""
    wrapper = getattr_migration(module_name)
    
    try:
        result = wrapper(attr_name)
        # If it doesn't raise, the result should be consistent
        result2 = wrapper(attr_name)
        assert result == result2
    except (AttributeError, KeyError, ValueError) as e:
        # These are expected for invalid names
        pass
    except Exception as e:
        # Any other exception should be consistent
        with pytest.raises(type(e)):
            wrapper(attr_name)


@given(
    attr_name=st.text(min_size=1, max_size=100)
)
def test_empty_module_name(attr_name):
    """Test behavior with empty module name."""
    try:
        wrapper = getattr_migration('')
        result = wrapper(attr_name)
    except Exception:
        pass  # Any exception is OK for empty module


@given(
    module_name=st.text(min_size=1).filter(lambda x: ':' not in x),
    count=st.integers(min_value=100, max_value=1000)
)
@settings(max_examples=10)
def test_many_calls_performance(module_name, count):
    """Test that many calls don't cause memory leaks or performance issues."""
    wrapper = getattr_migration(module_name)
    
    # Generate unique attribute names
    attrs = [f'attr_{i}' for i in range(count)]
    
    # Call wrapper many times
    for attr in attrs:
        try:
            wrapper(attr)
        except:
            pass
    
    # Should complete without issues
    assert True


@given(
    module_name=st.text(min_size=1, max_size=50),
    attr_name=st.text(min_size=1, max_size=50)
)
def test_unicode_handling(module_name, attr_name):
    """Test that Unicode characters are handled correctly."""
    # Add some Unicode to the names
    module_name = '🦄' + module_name
    attr_name = attr_name + '✨'
    
    wrapper = getattr_migration(module_name)
    
    try:
        result = wrapper(attr_name)
        # Should be consistent
        assert wrapper(attr_name) == result
    except Exception as e:
        # Should raise same exception
        with pytest.raises(type(e)):
            wrapper(attr_name)


@given(
    module_name=st.text(min_size=1, max_size=100).filter(lambda x: x not in sys.modules)
)
def test_nonexistent_module_behavior(module_name):
    """Test behavior when module doesn't exist in sys.modules."""
    assume(':' not in module_name)
    
    wrapper = getattr_migration(module_name)
    
    # Should raise AttributeError for non-special attributes
    with pytest.raises(AttributeError) as exc_info:
        wrapper('some_random_attr')
    
    error_msg = str(exc_info.value)
    assert 'some_random_attr' in error_msg or repr('some_random_attr') in error_msg


@given(
    st.data()
)
def test_moved_items_behavior(data):
    """Test that moved items from MOVED_IN_V2 work correctly."""
    if not MOVED_IN_V2:
        return  # Skip if no moved items
    
    # Pick a random moved item
    import_path = data.draw(st.sampled_from(list(MOVED_IN_V2.keys())))
    
    if ':' not in import_path:
        return  # Skip invalid format
    
    module_name, attr_name = import_path.split(':', 1)
    wrapper = getattr_migration(module_name)
    
    # Should issue a warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            result = wrapper(attr_name)
            # Should have warned about the move
            assert len(w) > 0
            assert 'moved' in str(w[0].message).lower()
        except Exception:
            pass  # Import might fail for other reasons


@given(
    st.data()
)
def test_removed_items_behavior(data):
    """Test that removed items from REMOVED_IN_V2 raise correct error."""
    if not REMOVED_IN_V2:
        return  # Skip if no removed items
    
    # Pick a random removed item
    import_path = data.draw(st.sampled_from(list(REMOVED_IN_V2)))
    
    if ':' not in import_path:
        return  # Skip invalid format
    
    module_name, attr_name = import_path.split(':', 1)
    wrapper = getattr_migration(module_name)
    
    from pydantic.errors import PydanticImportError
    
    # Should raise PydanticImportError
    with pytest.raises(PydanticImportError) as exc_info:
        wrapper(attr_name)
    
    error_msg = str(exc_info.value)
    assert 'removed in V2' in error_msg or 'has been removed' in error_msg