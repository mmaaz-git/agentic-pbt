import os
import sys

# Add virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

import django
from django.conf import settings
from django.db import models
from hypothesis import given, strategies as st, settings as h_settings, assume
import string
import re

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


# Test 1: History model naming consistency
@given(
    model_name=st.text(
        alphabet=string.ascii_letters + string.digits + '_',
        min_size=1,
        max_size=50
    ).filter(lambda x: x[0].isalpha() and not x.startswith('Historical'))
)
def test_history_model_name_generation(model_name):
    """Test that get_history_model_name produces consistent, valid names"""
    hr = HistoricalRecords()
    
    # Create a mock model class
    class MockMeta:
        object_name = model_name
    
    class MockModel:
        _meta = MockMeta()
        __module__ = 'test_module'
    
    # Test default naming
    history_name = hr.get_history_model_name(MockModel)
    
    # Property 1: History model name should start with "Historical"
    assert history_name.startswith("Historical"), f"History model name '{history_name}' should start with 'Historical'"
    
    # Property 2: History model name should contain original model name
    assert model_name in history_name, f"History model name '{history_name}' should contain original model name '{model_name}'"
    
    # Property 3: History model name should be different from original
    assert history_name != model_name, f"History model name should differ from original model name '{model_name}'"


# Test 2: Custom model name validation
@given(
    model_name=st.text(
        alphabet=string.ascii_letters + string.digits + '_',
        min_size=1,
        max_size=50
    ).filter(lambda x: x[0].isalpha()),
    custom_name=st.text(
        alphabet=string.ascii_letters + string.digits + '_',
        min_size=1,
        max_size=50
    ).filter(lambda x: x[0].isalpha())
)
def test_custom_history_model_name_validation(model_name, custom_name):
    """Test that custom model names are validated correctly"""
    hr = HistoricalRecords(custom_model_name=custom_name)
    hr.module = 'test_module'
    
    class MockMeta:
        object_name = model_name
    
    class MockModel:
        _meta = MockMeta()
        __module__ = 'test_module'
    
    # If custom name equals model name (case-insensitive), it should raise ValueError
    if custom_name.lower() == model_name.lower():
        try:
            history_name = hr.get_history_model_name(MockModel)
            # Should have raised an error
            assert False, f"Should have raised ValueError for conflicting names: model='{model_name}', custom='{custom_name}'"
        except ValueError as e:
            # Expected behavior - names conflict
            assert "same as the model it is tracking" in str(e)
    else:
        # Should work fine
        history_name = hr.get_history_model_name(MockModel)
        assert history_name == custom_name, f"Custom name '{custom_name}' should be used as-is"


# Test 3: Primary key name extraction
@given(
    pk_name=st.text(
        alphabet=string.ascii_lowercase + '_',
        min_size=1,
        max_size=30
    ).filter(lambda x: x[0].isalpha() and not x.endswith('_id'))
)
def test_primary_key_name_extraction(pk_name):
    """Test that primary key name extraction handles ForeignKey PKs correctly"""
    
    # Create mock model with regular field as PK
    class MockField:
        def __init__(self, name):
            self.name = name
            self.attname = name
    
    class MockMeta:
        def __init__(self, pk):
            self.pk = pk
    
    class MockModel:
        def __init__(self, pk_field):
            self._meta = MockMeta(pk_field)
    
    # Test regular field
    regular_field = MockField(pk_name)
    model = MockModel(regular_field)
    result = get_app_model_primary_key_name(model)
    assert result == pk_name, f"Regular field PK name should be '{pk_name}', got '{result}'"
    
    # Test ForeignKey field - should add '_id' suffix
    class MockForeignKey(MockField):
        pass
    
    # Override isinstance check for ForeignKey
    from unittest.mock import patch
    with patch('simple_history.utils.isinstance', side_effect=lambda obj, cls: cls == models.ForeignKey and isinstance(obj, MockForeignKey)):
        fk_field = MockForeignKey(pk_name)
        model_fk = MockModel(fk_field)
        result_fk = get_app_model_primary_key_name(model_fk)
        assert result_fk == f"{pk_name}_id", f"ForeignKey PK should have '_id' suffix: expected '{pk_name}_id', got '{result_fk}'"


# Test 4: No database index field validation
@given(
    fields=st.lists(
        st.text(alphabet=string.ascii_lowercase + '_', min_size=1, max_size=20),
        min_size=0,
        max_size=5,
        unique=True
    )
)
def test_no_db_index_normalization(fields):
    """Test that no_db_index field is properly normalized to a list"""
    
    # Test with list input
    hr_list = HistoricalRecords(no_db_index=fields)
    assert hr_list.no_db_index == fields, "List input should be preserved"
    assert isinstance(hr_list.no_db_index, list), "Should be a list"
    
    # Test with string input - should be converted to list
    if fields:
        single_field = fields[0]
        hr_string = HistoricalRecords(no_db_index=single_field)
        assert hr_string.no_db_index == [single_field], f"String '{single_field}' should be converted to list"
        assert isinstance(hr_string.no_db_index, list), "Should be a list after conversion"


# Test 5: Excluded fields handling
@given(
    excluded=st.one_of(
        st.none(),
        st.lists(
            st.text(alphabet=string.ascii_lowercase + '_', min_size=1, max_size=20),
            min_size=0,
            max_size=5
        )
    )
)
def test_excluded_fields_initialization(excluded):
    """Test that excluded_fields is properly initialized"""
    hr = HistoricalRecords(excluded_fields=excluded)
    
    if excluded is None:
        assert hr.excluded_fields == [], "None should be converted to empty list"
    else:
        assert hr.excluded_fields == excluded, "Excluded fields should be preserved"
    
    # Property: excluded_fields should always be a list
    assert isinstance(hr.excluded_fields, list), "excluded_fields should always be a list"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])