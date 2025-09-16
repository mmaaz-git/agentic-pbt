import sys
import warnings
from hypothesis import given, strategies as st, assume, settings
import pydantic.class_validators
import pydantic._migration
from pydantic.errors import PydanticImportError


# Edge case 1: Test with Unicode and special characters in attribute names
@given(st.text(min_size=1, max_size=50))
def test_unicode_attribute_names(attr_name):
    """Test that non-ASCII characters in attribute names are handled correctly."""
    # Skip valid Python identifiers (already tested)
    assume(not attr_name.isidentifier())
    assume(not attr_name.startswith('_'))
    assume(attr_name != '__path__')
    
    try:
        getattr(pydantic.class_validators, attr_name)
        # If it doesn't raise, it should be something special
        assert False, f"Expected AttributeError for non-identifier: {attr_name!r}"
    except AttributeError as e:
        # Should get a proper error message
        assert 'has no attribute' in str(e) or 'object has no attribute' in str(e)
    except Exception as e:
        # Any other exception is potentially a bug
        print(f"Unexpected exception for {attr_name!r}: {type(e).__name__}: {e}")
        raise


# Edge case 2: Test concurrent access to migrated attributes
@given(st.sampled_from(['validator', 'root_validator']))
def test_concurrent_attribute_access(attr_name):
    """Test that concurrent access to migrated attributes works correctly."""
    import threading
    results = []
    errors = []
    
    def access_attribute():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                obj = getattr(pydantic.class_validators, attr_name)
                results.append(obj)
        except Exception as e:
            errors.append(e)
    
    threads = [threading.Thread(target=access_attribute) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert len(errors) == 0, f"Concurrent access failed: {errors}"
    assert len(results) == 10, f"Not all threads completed"
    # All should get the same object
    assert all(obj is results[0] for obj in results), "Different objects returned"


# Edge case 3: Test sys.modules manipulation
def test_module_removal_handling():
    """Test behavior when pydantic modules are removed from sys.modules."""
    wrapper = pydantic._migration.getattr_migration('pydantic.class_validators')
    
    # Save current state
    saved_modules = {}
    for key in list(sys.modules.keys()):
        if 'pydantic' in key:
            saved_modules[key] = sys.modules[key]
    
    try:
        # Remove pydantic.deprecated modules
        for key in list(sys.modules.keys()):
            if 'pydantic.deprecated' in key:
                del sys.modules[key]
        
        # Should still work by re-importing
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            validator = wrapper('validator')
            assert callable(validator), "Should still get validator after module removal"
            
    finally:
        # Restore modules
        sys.modules.update(saved_modules)


# Edge case 4: Test with extremely long attribute names
@given(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), 
               min_size=1000, max_size=5000))
def test_very_long_attribute_names(long_name):
    """Test handling of very long attribute names."""
    try:
        getattr(pydantic.class_validators, long_name)
        assert False, f"Should have raised AttributeError for long name"
    except AttributeError as e:
        # Should handle gracefully without memory issues
        assert 'has no attribute' in str(e)
    except MemoryError:
        assert False, "Should not raise MemoryError for long attribute names"


# Edge case 5: Test import_string with special module names
@given(st.sampled_from([
    '',  # Empty string
    ' ',  # Just whitespace
    '\n',  # Newline
    '\t',  # Tab
    'None',  # Reserved word
    'True',  # Reserved word
    'False',  # Reserved word
]))
def test_import_string_special_inputs(module_name):
    """Test import_string with special/reserved string inputs - should fail."""
    from pydantic._internal._validators import import_string
    
    # These are strings, so import_string will try to import them
    try:
        result = import_string(module_name)
        # Some might succeed if they're valid module names
        if module_name in ['', ' ', '\n', '\t']:
            assert False, f"Should have failed for invalid module name: {module_name!r}"
    except Exception as e:
        # Should get an appropriate error for invalid module names
        assert 'Invalid python path' in str(e) or 'No module named' in str(e)


# Edge case 6: Test wrapper with None and other types
@given(st.one_of(st.none(), st.integers(), st.floats(), st.lists(st.integers())))
def test_wrapper_with_non_string_attributes(attr_value):
    """Test that the wrapper handles non-string attribute names correctly."""
    wrapper = pydantic._migration.getattr_migration('pydantic.class_validators')
    
    try:
        wrapper(attr_value)
        assert False, f"Should have raised TypeError or AttributeError for {type(attr_value)}"
    except (TypeError, AttributeError):
        pass  # Expected


# Edge case 7: Test import_string with actual malicious paths
@given(st.sampled_from([
    ':::',  # Multiple colons
    'os:system',  # Potentially dangerous
    '__import__:__builtins__',  # Access to builtins
    'sys:exit',  # System exit
    'eval:__builtins__',  # eval access
]))
def test_import_string_dangerous_paths(path):
    """Test that import_string handles potentially dangerous paths safely."""
    from pydantic._internal._validators import import_string
    
    try:
        result = import_string(path)
        # If it succeeds, verify it's actually importing what it claims
        if ':' in path and path.count(':') > 1:
            assert False, f"Should fail with multiple colons: {path}"
    except Exception:
        pass  # Any exception is fine for dangerous paths


# Edge case 8: Test attribute access with modified __dict__
def test_modified_module_dict():
    """Test behavior when module __dict__ is modified."""
    # Add a custom attribute to the module
    pydantic.class_validators.__dict__['custom_attr'] = lambda: "custom"
    
    try:
        # Should be accessible through normal getattr
        result = getattr(pydantic.class_validators, 'custom_attr')
        assert callable(result), "Custom attribute should be accessible"
        assert result() == "custom", "Custom attribute should work"
    finally:
        # Clean up
        if 'custom_attr' in pydantic.class_validators.__dict__:
            del pydantic.class_validators.__dict__['custom_attr']


# Edge case 9: Test rapid repeated access
@given(st.sampled_from(['validator', 'root_validator']), 
       st.integers(min_value=100, max_value=1000))
@settings(max_examples=10)
def test_rapid_repeated_access(attr_name, num_accesses):
    """Test that rapid repeated access doesn't cause issues."""
    results = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _ in range(num_accesses):
            obj = getattr(pydantic.class_validators, attr_name)
            results.append(obj)
    
    # All should be the same object
    assert all(obj is results[0] for obj in results), "Repeated access should return same object"
    assert len(results) == num_accesses, "All accesses should succeed"