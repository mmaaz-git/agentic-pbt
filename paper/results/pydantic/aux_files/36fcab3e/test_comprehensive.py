"""Comprehensive test with increased examples to find edge cases."""
import warnings
from hypothesis import given, strategies as st, settings, HealthCheck
import pydantic.class_validators
import pydantic._migration


# Test with many more examples to find edge cases
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=1000, suppress_health_check=[HealthCheck.filter_too_much])
def test_comprehensive_attribute_access(attr_name):
    """Comprehensive test of attribute access with many examples."""
    # Special attributes that should work
    special_attrs = {
        'validator', 'root_validator', '__name__', '__file__', '__doc__',
        '__package__', '__loader__', '__spec__', '__getattr__', 'getattr_migration',
        '__dict__', '__module__', '__weakref__', '__class__', '__repr__',
        '__hash__', '__str__', '__dir__', '__sizeof__', '__reduce__',
        '__reduce_ex__', '__subclasshook__', '__init_subclass__', '__format__',
        '__new__', '__init__', '__delattr__', '__setattr__', '__getattribute__',
        '__eq__', '__ne__', '__lt__', '__le__', '__gt__', '__ge__'
    }
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        
        try:
            result = getattr(pydantic.class_validators, attr_name)
            # If it succeeds, it should be a known attribute
            assert attr_name in special_attrs or hasattr(pydantic.class_validators, attr_name), \
                f"Unexpected success for {attr_name!r}"
        except AttributeError as e:
            # __path__ is special - always raises
            if attr_name == '__path__':
                assert 'has no attribute' in str(e)
            # Other non-existent attributes
            elif attr_name not in special_attrs:
                assert 'has no attribute' in str(e) or 'object has no attribute' in str(e)
            else:
                # Known attributes shouldn't raise AttributeError
                raise


# Test import_string with diverse inputs
@given(st.one_of(
    st.text(min_size=0, max_size=100),
    st.text().map(lambda x: f"{x}:{x}"),
    st.text().map(lambda x: f":{x}"),
    st.text().map(lambda x: f"{x}:"),
))
@settings(max_examples=500)
def test_comprehensive_import_string(import_path):
    """Test import_string with diverse string inputs."""
    from pydantic._internal._validators import import_string
    
    try:
        result = import_string(import_path)
        # If it succeeds, verify it's a valid import
        if ':' in import_path:
            parts = import_path.split(':')
            if len(parts) > 2:
                assert False, f"Should fail with multiple colons: {import_path}"
            if not parts[0] or not parts[0].strip():
                assert False, f"Should fail with empty module: {import_path}"
    except Exception as e:
        # Various failure modes are acceptable
        error_str = str(e)
        valid_errors = [
            'Invalid python path',
            'No module named',
            'Import strings should have',
            'cannot import name',
            'has no attribute'
        ]
        assert any(err in error_str for err in valid_errors), \
            f"Unexpected error message: {error_str}"


# Test wrapper behavior with edge cases
@given(st.text(min_size=0, max_size=200))
@settings(max_examples=500)
def test_comprehensive_wrapper_behavior(attr_name):
    """Test getattr_migration wrapper with many inputs."""
    wrapper = pydantic._migration.getattr_migration('pydantic.class_validators')
    
    try:
        result = wrapper(attr_name)
        # If successful, should be a valid attribute
        if attr_name == '__path__':
            assert False, "__path__ should always raise"
    except AttributeError as e:
        # Expected for non-existent attributes
        if attr_name == '__path__':
            assert 'has no attribute' in str(e)
        else:
            assert 'has no attribute' in str(e) or 'object has no attribute' in str(e)
    except Exception as e:
        # Other exceptions might indicate bugs
        if not isinstance(e, (ImportError, TypeError)):
            print(f"Unexpected exception for {attr_name!r}: {type(e).__name__}: {e}")
            raise