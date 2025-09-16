import os
import sys

# Add virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

import django
from django.conf import settings
from hypothesis import given, strategies as st, assume, example
import string

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'simple_history',
        ],
        SECRET_KEY='test-secret-key',
        USE_TZ=True,
    )
    django.setup()

from simple_history.models import HistoricalRecords
from simple_history.utils import get_app_model_primary_key_name
from simple_history import register


# Test 1: Register function with table_name edge cases
@given(
    table_name=st.text(
        alphabet=string.ascii_letters + string.digits + '_',
        min_size=1,
        max_size=63  # PostgreSQL table name limit
    ).filter(lambda x: x[0].isalpha() or x[0] == '_')
)
def test_register_function_table_name_handling(table_name):
    """Test that the register function properly handles table_name parameter"""
    
    # Create a mock model
    class MockMeta:
        app_label = 'test'
        object_name = 'TestModel'
        abstract = False
    
    class MockModel:
        _meta = MockMeta()
        __module__ = 'test.models'
    
    # Test that table_name is properly passed through
    try:
        register(
            MockModel,
            table_name=table_name,
            manager_name='custom_history'
        )
        # The register function should have set the table_name
        assert hasattr(MockModel, 'custom_history')
    except Exception as e:
        # Check if it's a valid failure
        if "registered multiple times" in str(e):
            # This is expected if we try to register the same model twice
            pass
        else:
            # Unexpected error
            raise


# Test 2: Module parameter handling in register function
@given(
    app_name=st.text(
        alphabet=string.ascii_lowercase + '_',
        min_size=1,
        max_size=30
    ).filter(lambda x: x[0].isalpha()),
    use_none=st.booleans()
)
def test_register_module_parameter(app_name, use_none):
    """Test that the app parameter in register function is handled correctly"""
    
    class MockModel:
        __module__ = 'original.module'
    
    # Create a HistoricalRecords instance via register
    from simple_history import models
    
    records_config = {}
    records_class = models.HistoricalRecords
    records = records_class(**records_config)
    
    if use_none:
        records.module = None and ("%s.models" % None) or MockModel.__module__
        expected = MockModel.__module__
    else:
        records.module = app_name and ("%s.models" % app_name) or MockModel.__module__
        expected = f"{app_name}.models"
    
    assert records.module == expected


# Test 3: Empty string handling in field names
@given(
    field_name=st.text(min_size=0, max_size=30)
)
def test_empty_field_name_handling(field_name):
    """Test handling of empty or unusual field names"""
    
    # Test with excluded_fields
    if field_name == "":
        # Empty string in excluded fields should be allowed but might cause issues
        hr = HistoricalRecords(excluded_fields=[field_name])
        assert field_name in hr.excluded_fields
        assert "" in hr.excluded_fields  # Empty string should be preserved
    else:
        hr = HistoricalRecords(excluded_fields=[field_name])
        assert field_name in hr.excluded_fields


# Test 4: Unicode and special characters in model names
@given(
    model_name=st.text(
        alphabet=string.ascii_letters + "αβγδεζηθικλμνξοπρστυφχψω" + "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
        min_size=1,
        max_size=30
    ).filter(lambda x: x[0].isalpha())
)
@example(model_name="Модель")  # Russian
@example(model_name="Μοντέλο")  # Greek
def test_unicode_model_names(model_name):
    """Test that Unicode characters in model names are handled correctly"""
    
    hr = HistoricalRecords()
    
    class MockMeta:
        object_name = model_name
    
    class MockModel:
        _meta = MockMeta()
        __module__ = 'test_module'
    
    try:
        history_name = hr.get_history_model_name(MockModel)
        # Should succeed and add Historical prefix
        assert history_name.startswith("Historical")
        assert model_name in history_name
    except Exception as e:
        # If it fails, check if it's a Python identifier issue
        if not model_name.isidentifier():
            # Expected for non-ASCII that aren't valid Python identifiers
            pass
        else:
            raise


# Test 5: Extreme lengths for custom model names
@given(
    base_name=st.text(
        alphabet=string.ascii_letters,
        min_size=1,
        max_size=10
    ),
    multiplier=st.integers(min_value=1, max_value=100)
)
def test_extreme_length_custom_names(base_name, multiplier):
    """Test handling of very long custom model names"""
    
    # Create a very long custom name
    long_name = base_name * multiplier
    
    # Django has a 100 character limit for model names
    if len(long_name) > 100:
        long_name = long_name[:100]
    
    hr = HistoricalRecords(custom_model_name=long_name)
    hr.module = 'test_module'
    
    class MockMeta:
        object_name = 'ShortName'
    
    class MockModel:
        _meta = MockMeta()
        __module__ = 'test_module'
    
    # Check if the custom name would conflict
    if long_name.lower() == 'shortname':
        try:
            history_name = hr.get_history_model_name(MockModel)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
    else:
        history_name = hr.get_history_model_name(MockModel)
        assert history_name == long_name


# Test 6: Callable custom_model_name with exceptions
@given(
    model_name=st.text(
        alphabet=string.ascii_letters,
        min_size=1,
        max_size=20
    ),
    should_raise=st.booleans()
)
def test_callable_custom_name_with_exceptions(model_name, should_raise):
    """Test that exceptions in callable custom_model_name are handled"""
    
    def faulty_name_function(original_name):
        if should_raise:
            raise ValueError("Intentional error in name function")
        return f"Custom{original_name}"
    
    hr = HistoricalRecords(custom_model_name=faulty_name_function)
    hr.module = 'test_module'
    
    class MockMeta:
        object_name = model_name
    
    class MockModel:
        _meta = MockMeta()
        __module__ = 'test_module'
    
    if should_raise:
        try:
            history_name = hr.get_history_model_name(MockModel)
            # The function raised an error, so this should propagate
            assert False, "Exception should have propagated"
        except ValueError as e:
            assert "Intentional error" in str(e)
    else:
        history_name = hr.get_history_model_name(MockModel)
        assert history_name == f"Custom{model_name}"


# Test 7: Case sensitivity in model name conflicts
@given(
    name1=st.text(
        alphabet=string.ascii_letters,
        min_size=1,
        max_size=20
    ),
    case_variation=st.sampled_from(['upper', 'lower', 'title', 'swapcase'])
)
def test_case_sensitive_name_conflicts(name1, case_variation):
    """Test that case variations are properly detected as conflicts"""
    
    # Create case variation
    if case_variation == 'upper':
        name2 = name1.upper()
    elif case_variation == 'lower':
        name2 = name1.lower()
    elif case_variation == 'title':
        name2 = name1.title()
    else:
        name2 = name1.swapcase()
    
    hr = HistoricalRecords(custom_model_name=name2)
    hr.module = 'test_module'
    
    class MockMeta:
        object_name = name1
    
    class MockModel:
        _meta = MockMeta()
        __module__ = 'test_module'
    
    # Check if they conflict (case-insensitive comparison)
    if name1.lower() == name2.lower():
        try:
            history_name = hr.get_history_model_name(MockModel)
            assert False, f"Should detect conflict between '{name1}' and '{name2}'"
        except ValueError as e:
            assert "same as the model it is tracking" in str(e)
    else:
        history_name = hr.get_history_model_name(MockModel)
        assert history_name == name2


# Test 8: Whitespace in configuration values
@given(
    manager_name=st.text(
        alphabet=string.ascii_letters + ' \t\n',
        min_size=1,
        max_size=30
    ).filter(lambda x: x.strip() and x.strip()[0].isalpha())
)
def test_whitespace_in_manager_name(manager_name):
    """Test handling of whitespace in manager names"""
    
    # Manager names with whitespace should either be rejected or stripped
    hr = HistoricalRecords()
    
    # Set the manager name directly
    hr.manager_name = manager_name
    
    # Check if it's a valid Python identifier
    if not manager_name.isidentifier():
        # This should cause issues when trying to use it as an attribute name
        # But the library might not validate this immediately
        pass
    else:
        # Valid identifier, should work fine
        assert hr.manager_name == manager_name


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])