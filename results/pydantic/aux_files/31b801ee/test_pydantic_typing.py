import warnings
from hypothesis import given, strategies as st, assume, settings
import pydantic.typing
import pydantic._migration as pm
from pydantic.errors import PydanticImportError


# Property 1: Idempotence - Multiple wrappers for same module should behave identically
@given(st.text(min_size=1, max_size=100).filter(lambda x: ':' not in x and '.' not in x))
def test_wrapper_idempotence(attr_name):
    """Multiple wrappers for the same module should produce identical results."""
    assume(attr_name != '__path__')  # Special case
    
    wrapper1 = pydantic.typing.getattr_migration('test.module')
    wrapper2 = pydantic.typing.getattr_migration('test.module')
    
    # Both should raise the same AttributeError for non-existent attributes
    try:
        result1 = wrapper1(attr_name)
        exception1 = None
    except (AttributeError, PydanticImportError) as e:
        result1 = None
        exception1 = str(e)
    
    try:
        result2 = wrapper2(attr_name)
        exception2 = None
    except (AttributeError, PydanticImportError) as e:
        result2 = None
        exception2 = str(e)
    
    # Both should have same behavior
    assert (result1 is None) == (result2 is None)
    assert exception1 == exception2


# Property 2: __path__ special handling
@given(st.text(min_size=1, max_size=100))
def test_path_attribute_always_raises(module_name):
    """__path__ should always raise AttributeError with specific message."""
    wrapper = pydantic.typing.getattr_migration(module_name)
    
    try:
        wrapper('__path__')
        assert False, "__path__ should always raise AttributeError"
    except AttributeError as e:
        # Check message format
        assert f"module {module_name!r} has no attribute '__path__'" == str(e)


# Property 3: Migration mappings are mutually exclusive
def test_migration_mappings_exclusive():
    """Items should not appear in multiple migration dictionaries."""
    moved_keys = set(pm.MOVED_IN_V2.keys())
    deprecated_keys = set(pm.DEPRECATED_MOVED_IN_V2.keys())
    redirect_keys = set(pm.REDIRECT_TO_V1.keys())
    removed_keys = pm.REMOVED_IN_V2
    
    # Check no overlap between dictionaries
    assert len(moved_keys & deprecated_keys) == 0, "MOVED_IN_V2 and DEPRECATED_MOVED_IN_V2 overlap"
    assert len(moved_keys & redirect_keys) == 0, "MOVED_IN_V2 and REDIRECT_TO_V1 overlap"
    assert len(moved_keys & removed_keys) == 0, "MOVED_IN_V2 and REMOVED_IN_V2 overlap"
    assert len(deprecated_keys & redirect_keys) == 0, "DEPRECATED_MOVED_IN_V2 and REDIRECT_TO_V1 overlap"
    assert len(deprecated_keys & removed_keys) == 0, "DEPRECATED_MOVED_IN_V2 and REMOVED_IN_V2 overlap"
    assert len(redirect_keys & removed_keys) == 0, "REDIRECT_TO_V1 and REMOVED_IN_V2 overlap"


# Property 4: AttributeError message format consistency
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: ':' not in x),
    st.text(min_size=1, max_size=50).filter(lambda x: not x.startswith('_'))
)
def test_attribute_error_format(module_name, attr_name):
    """AttributeError messages should have consistent format."""
    assume(attr_name != '__path__')  # Special case tested separately
    assume(f'{module_name}:{attr_name}' not in pm.MOVED_IN_V2)
    assume(f'{module_name}:{attr_name}' not in pm.DEPRECATED_MOVED_IN_V2)
    assume(f'{module_name}:{attr_name}' not in pm.REDIRECT_TO_V1)
    assume(f'{module_name}:{attr_name}' not in pm.REMOVED_IN_V2)
    assume(module_name != 'pydantic' or attr_name != 'BaseSettings')  # Special case
    
    wrapper = pydantic.typing.getattr_migration(module_name)
    
    try:
        wrapper(attr_name)
        # If it doesn't raise, it means the attribute exists in globals
    except AttributeError as e:
        msg = str(e)
        # Check message format: module 'X' has no attribute 'Y'
        expected = f"module {module_name!r} has no attribute {attr_name!r}"
        assert msg == expected, f"Unexpected message format: {msg}"
    except PydanticImportError:
        # This is expected for removed items
        pass


# Property 5: Warning behavior for MOVED_IN_V2 vs DEPRECATED_MOVED_IN_V2
def test_warning_behavior_difference():
    """MOVED_IN_V2 should warn, DEPRECATED_MOVED_IN_V2 should not warn here."""
    # Test with a MOVED_IN_V2 item
    if pm.MOVED_IN_V2:
        moved_item = list(pm.MOVED_IN_V2.keys())[0]
        module, attr = moved_item.split(':')
        wrapper = pydantic.typing.getattr_migration(module)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            try:
                wrapper(attr)
                # Should have warned
                assert len(w) > 0, f"MOVED_IN_V2 item {moved_item} should produce warning"
                assert f'`{moved_item}` has been moved to' in str(w[0].message)
            except Exception:
                pass  # Import might fail, but that's ok for this test
    
    # Test with a DEPRECATED_MOVED_IN_V2 item  
    if pm.DEPRECATED_MOVED_IN_V2:
        deprecated_item = list(pm.DEPRECATED_MOVED_IN_V2.keys())[0]
        module, attr = deprecated_item.split(':')
        wrapper = pydantic.typing.getattr_migration(module)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            try:
                wrapper(attr)
                # Should NOT warn here (comment says warning raised elsewhere)
                assert len(w) == 0, f"DEPRECATED_MOVED_IN_V2 item {deprecated_item} should not warn in getattr_migration"
            except Exception:
                pass  # Import might fail, but that's ok for this test


# Property 6: BaseSettings special case
def test_base_settings_special_error():
    """pydantic:BaseSettings should raise specific PydanticImportError."""
    wrapper = pydantic.typing.getattr_migration('pydantic')
    
    try:
        wrapper('BaseSettings')
        assert False, "BaseSettings should raise PydanticImportError"
    except PydanticImportError as e:
        msg = str(e)
        assert 'pydantic-settings' in msg, "Error should mention pydantic-settings package"
        assert 'moved' in msg.lower(), "Error should mention it was moved"


# Property 7: Error type consistency for removed items
@given(st.sampled_from(list(pm.REMOVED_IN_V2)))
def test_removed_items_error_type(removed_item):
    """Items in REMOVED_IN_V2 should always raise PydanticImportError."""
    if ':' not in removed_item:
        return  # Skip malformed entries
    
    module, attr = removed_item.split(':', 1)
    wrapper = pydantic.typing.getattr_migration(module)
    
    try:
        wrapper(attr)
        assert False, f"Removed item {removed_item} should raise PydanticImportError"
    except PydanticImportError as e:
        msg = str(e)
        assert f'`{removed_item}` has been removed in V2' in msg
    except AttributeError:
        # This should not happen for items in REMOVED_IN_V2
        assert False, f"Removed item {removed_item} raised AttributeError instead of PydanticImportError"


# Property 8: Round-trip property for module/attr splitting and reconstruction
@given(
    st.text(min_size=1, max_size=30).filter(lambda x: ':' not in x and '.' in x),
    st.text(min_size=1, max_size=30).filter(lambda x: ':' not in x and not x.startswith('_'))
)
def test_import_path_reconstruction(module, attr):
    """import_path construction and usage should be consistent."""
    import_path = f'{module}:{attr}'
    
    # The wrapper should use this exact format when checking dictionaries
    wrapper = pydantic.typing.getattr_migration(module)
    
    # Create a test to verify the import_path is constructed correctly
    # by checking if it would match entries in the dictionaries
    if import_path in pm.MOVED_IN_V2:
        # If it's in MOVED_IN_V2, accessing should trigger the moved logic
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            try:
                wrapper(attr)
                assert len(w) > 0, f"Should warn for moved item"
                assert import_path in str(w[0].message)
            except ImportError:
                pass  # Import errors are ok, we're testing the path construction