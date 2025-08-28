import warnings
import sys
from hypothesis import given, strategies as st, assume, settings
import pydantic.class_validators
import pydantic._migration
from pydantic.errors import PydanticImportError


# Property 1: Accessing known migrated attributes should return consistent objects
@given(st.sampled_from(['validator', 'root_validator']))
def test_migrated_attributes_are_consistent(attr_name):
    """Migrated attributes should always return the same object when accessed multiple times."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # Ignore migration warnings for this test
        obj1 = getattr(pydantic.class_validators, attr_name)
        obj2 = getattr(pydantic.class_validators, attr_name)
        assert obj1 is obj2, f"Multiple accesses to {attr_name} should return the same object"
        assert callable(obj1), f"{attr_name} should be callable"


# Property 2: Non-existent attributes should consistently raise AttributeError
@given(st.text(min_size=1, max_size=100).filter(
    lambda x: x not in ['validator', 'root_validator', '__path__', '__name__', '__file__', '__doc__', 
                        '__package__', '__loader__', '__spec__', '__getattr__', 'getattr_migration']
    and not x.startswith('_')
    and x.isidentifier()
))
def test_nonexistent_attributes_raise_attribute_error(attr_name):
    """Non-existent attributes should raise AttributeError with consistent message format."""
    try:
        getattr(pydantic.class_validators, attr_name)
        assert False, f"Should have raised AttributeError for {attr_name}"
    except AttributeError as e:
        error_msg = str(e)
        assert 'pydantic.class_validators' in error_msg
        assert attr_name in error_msg
        assert "has no attribute" in error_msg


# Property 3: __path__ should always raise AttributeError (special case in code)
def test_path_attribute_always_raises():
    """__path__ attribute should always raise AttributeError per the implementation."""
    try:
        pydantic.class_validators.__path__
        assert False, "__path__ should always raise AttributeError"
    except AttributeError as e:
        assert "__path__" in str(e)
        assert "has no attribute" in str(e)


# Property 4: Deprecated validators should not issue warnings at migration level
@given(st.sampled_from(['validator', 'root_validator']))
def test_deprecated_attributes_no_migration_warnings(attr_name):
    """Deprecated attributes in DEPRECATED_MOVED_IN_V2 should not issue warnings at migration level."""
    # Per the code comment: "skip the warning here because a deprecation warning will be raised elsewhere"
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        obj = getattr(pydantic.class_validators, attr_name)
        # These are in DEPRECATED_MOVED_IN_V2, so no warnings at migration level
        migration_warnings = [warning for warning in w 
                             if 'has been moved' in str(warning.message)]
        assert len(migration_warnings) == 0, f"Should not issue migration warning for {attr_name}"
        # But the object should be successfully retrieved
        assert callable(obj), f"{attr_name} should be callable"


# Property 5: Test import_string idempotence
@given(st.sampled_from([
    'collections',
    'collections.abc',
    'collections.abc:Mapping',
    'typing:Dict',
    'sys:modules'
]))
def test_import_string_idempotence(import_path):
    """import_string should be idempotent - same input gives same output."""
    from pydantic._internal._validators import import_string
    
    obj1 = import_string(import_path)
    obj2 = import_string(import_path)
    assert obj1 is obj2, f"import_string({import_path}) should return the same object"


# Property 6: Test invalid import strings
@given(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=33, max_codepoint=126))
       .map(lambda x: f"{x}:a:b" if ':' not in x else x + ":a:b"))
@settings(suppress_health_check=[])
def test_import_string_multiple_colons_fails(import_path):
    """import_string should fail with multiple colons."""
    from pydantic._internal._validators import import_string
    assume(import_path.count(':') >= 2)  # Ensure we have multiple colons
    
    try:
        import_string(import_path)
        assert False, f"Should have raised error for {import_path} with multiple colons"
    except Exception as e:
        # Should raise ImportError or PydanticCustomError
        assert "Import strings should have at most one" in str(e) or "import_error" in str(type(e).__name__)


# Property 7: Empty module name should fail
@given(st.sampled_from([':', ':attr', '  :attr']))
def test_import_string_empty_module_fails(import_path):
    """import_string should fail with empty module name."""
    from pydantic._internal._validators import import_string
    
    try:
        import_string(import_path)
        assert False, f"Should have raised error for empty module in {import_path}"
    except Exception as e:
        assert "nonempty module name" in str(e) or "import_error" in str(type(e).__name__)


# Property 8: Test getattr_migration wrapper behavior
@given(st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier() and not x.startswith('_')))
def test_getattr_migration_wrapper_consistency(module_name):
    """getattr_migration should return a consistent wrapper function."""
    wrapper1 = pydantic._migration.getattr_migration(module_name)
    wrapper2 = pydantic._migration.getattr_migration(module_name)
    
    # Both should be callable
    assert callable(wrapper1)
    assert callable(wrapper2)
    
    # They don't need to be the same object, but should behave the same
    # Test with __path__ which should always raise
    try:
        wrapper1('__path__')
        assert False, "Should raise AttributeError for __path__"
    except AttributeError:
        pass
    
    try:
        wrapper2('__path__')
        assert False, "Should raise AttributeError for __path__"
    except AttributeError:
        pass


# Property 9: Test that BaseSettings raises specific error
def test_base_settings_import_error():
    """Accessing BaseSettings should raise PydanticImportError with specific message."""
    # Create a mock module to test the wrapper
    wrapper = pydantic._migration.getattr_migration('pydantic')
    
    # Temporarily modify sys.modules to simulate the scenario
    old_dict = sys.modules.get('pydantic', {}).__dict__.copy() if 'pydantic' in sys.modules else {}
    
    try:
        # Clear BaseSettings from globals if it exists
        if 'pydantic' in sys.modules and 'BaseSettings' in sys.modules['pydantic'].__dict__:
            del sys.modules['pydantic'].__dict__['BaseSettings']
        
        wrapper('BaseSettings')
        assert False, "Should raise PydanticImportError for BaseSettings"
    except PydanticImportError as e:
        assert 'pydantic-settings' in str(e)
        assert 'BaseSettings' in str(e)
    finally:
        # Restore original state
        if 'pydantic' in sys.modules:
            sys.modules['pydantic'].__dict__.update(old_dict)


# Property 10: Test metamorphic property - accessing through different paths
@given(st.sampled_from(['validator', 'root_validator']))
def test_metamorphic_access_paths(attr_name):
    """Accessing an attribute directly vs through getattr should yield same result."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        
        # Direct attribute access
        obj1 = getattr(pydantic.class_validators, attr_name)
        
        # Through __getattr__ explicitly
        obj2 = pydantic.class_validators.__getattr__(attr_name)
        
        assert obj1 is obj2, "Different access methods should return the same object"