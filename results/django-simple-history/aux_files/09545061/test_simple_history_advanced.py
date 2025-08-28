import os
import sys
import re

# Add virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

import django
from django.conf import settings
from django.db import models, connection
from django.test import TestCase
from django.apps import apps
from hypothesis import given, strategies as st, settings as h_settings, assume, example
import string
from datetime import datetime, timezone

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
        ALLOWED_HOSTS=['*'],
    )
    django.setup()

from simple_history.models import HistoricalRecords
from simple_history.utils import bulk_create_with_history, bulk_update_with_history
from simple_history.manager import HistoricalQuerySet
from django.contrib.auth import get_user_model


# Test 1: HistoricalQuerySet filter method with pk
@given(
    pk_values=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=5)
)
def test_historical_queryset_pk_filter_translation(pk_values):
    """Test that pk filtering works correctly when as_instances is True"""
    
    # Create a mock queryset
    class MockModel:
        class _meta:
            class pk:
                attname = "id"
        
    class MockHistoricalModel(models.Model):
        class Meta:
            app_label = 'test'
            abstract = True
        
        instance_type = MockModel
        history_type = models.CharField(max_length=1, default="+")
    
    qs = HistoricalQuerySet(model=MockHistoricalModel)
    
    # Test without as_instances - pk should remain as pk
    filtered = qs.filter(pk=pk_values[0])
    # Can't directly test the filter values, but we can verify the queryset state
    assert filtered._as_instances == False
    
    # Test with as_instances - pk should be translated to the original model's pk field
    instances_qs = qs.as_instances()
    assert instances_qs._as_instances == True
    
    # Now filter with pk - it should translate to 'id' internally
    filtered_instances = instances_qs.filter(pk=pk_values[0])
    assert filtered_instances._as_instances == True


# Test 2: Change reason preservation
@given(
    reason=st.text(min_size=1, max_size=100),
    field_value=st.text(min_size=1, max_size=50)
)
def test_change_reason_extraction(reason, field_value):
    """Test that change reasons are properly extracted from objects"""
    from simple_history.utils import get_change_reason_from_object
    
    # Test object without _change_reason
    class PlainObject:
        pass
    
    obj1 = PlainObject()
    assert get_change_reason_from_object(obj1) is None
    
    # Test object with _change_reason
    class ObjectWithReason:
        def __init__(self, reason):
            self._change_reason = reason
    
    obj2 = ObjectWithReason(reason)
    assert get_change_reason_from_object(obj2) == reason
    
    # Test object with None _change_reason
    obj3 = ObjectWithReason(None)
    assert get_change_reason_from_object(obj3) is None


# Test 3: Base class validation
@given(
    bases_input=st.one_of(
        st.text(min_size=1, max_size=20),  # Invalid string
        st.integers(),  # Invalid integer
        st.lists(st.just(models.Model), min_size=0, max_size=3),  # Valid list
        st.tuples(st.just(models.Model)),  # Valid tuple
    )
)
def test_historical_records_bases_validation(bases_input):
    """Test that bases parameter is properly validated"""
    
    if isinstance(bases_input, (list, tuple)):
        # Should work fine
        try:
            hr = HistoricalRecords(bases=bases_input)
            # Check that HistoricalChanges was added
            assert len(hr.bases) > len(bases_input) if bases_input else len(hr.bases) > 0
        except Exception as e:
            # Should not raise for valid inputs
            assert False, f"Valid bases input {type(bases_input)} raised exception: {e}"
    else:
        # Should raise TypeError for invalid inputs
        try:
            hr = HistoricalRecords(bases=bases_input)
            assert False, f"Invalid bases input {type(bases_input)} should have raised TypeError"
        except TypeError as e:
            assert "must be a list or a tuple" in str(e)


# Test 4: M2M bases validation  
@given(
    m2m_bases_input=st.one_of(
        st.text(min_size=1, max_size=20),  # Invalid string
        st.integers(),  # Invalid integer
        st.lists(st.just(models.Model), min_size=0, max_size=3),  # Valid list
        st.tuples(st.just(models.Model)),  # Valid tuple
    )
)
def test_historical_records_m2m_bases_validation(m2m_bases_input):
    """Test that m2m_bases parameter is properly validated"""
    
    if isinstance(m2m_bases_input, (list, tuple)):
        # Should work fine
        try:
            hr = HistoricalRecords(m2m_bases=m2m_bases_input)
            # Check that HistoricalChanges was added
            assert len(hr.m2m_bases) > len(m2m_bases_input) if m2m_bases_input else len(hr.m2m_bases) > 0
        except Exception as e:
            # Should not raise for valid inputs
            assert False, f"Valid m2m_bases input {type(m2m_bases_input)} raised exception: {e}"
    else:
        # Should raise TypeError for invalid inputs
        try:
            hr = HistoricalRecords(m2m_bases=m2m_bases_input)
            assert False, f"Invalid m2m_bases input {type(m2m_bases_input)} should have raised TypeError"
        except TypeError as e:
            assert "must be a list or a tuple" in str(e)


# Test 5: Historical model name edge cases
@given(
    model_name=st.text(
        alphabet=string.ascii_letters + string.digits,
        min_size=1,
        max_size=30
    ).filter(lambda x: x[0].isalpha())
)
@example(model_name="Historical")  # Edge case: model already starts with Historical
@example(model_name="Model")  # Simple case
@example(model_name="A")  # Single character
def test_historical_model_name_edge_cases(model_name):
    """Test edge cases in historical model naming"""
    
    hr = HistoricalRecords()
    
    class MockMeta:
        object_name = model_name
    
    class MockModel:
        _meta = MockMeta()
        __module__ = 'test_module'
    
    history_name = hr.get_history_model_name(MockModel)
    
    # Property: Should always prefix with "Historical"
    assert history_name.startswith("Historical")
    
    # Property: Should contain the original model name
    assert model_name in history_name
    
    # Property: Result should be a valid Python identifier
    assert history_name.isidentifier(), f"'{history_name}' is not a valid Python identifier"
    
    # Edge case: If model already starts with "Historical", we get "HistoricalHistorical..."
    if model_name.startswith("Historical"):
        assert history_name == f"Historical{model_name}"


# Test 6: Custom model name with callable
@given(
    model_name=st.text(
        alphabet=string.ascii_letters,
        min_size=1,
        max_size=20
    ).filter(lambda x: x[0].isalpha()),
    prefix=st.text(
        alphabet=string.ascii_letters,
        min_size=1,
        max_size=10
    ),
    suffix=st.text(
        alphabet=string.ascii_letters,  
        min_size=1,
        max_size=10
    )
)
def test_custom_model_name_callable(model_name, prefix, suffix):
    """Test that callable custom_model_name works correctly"""
    
    def name_function(original_name):
        return f"{prefix}{original_name}{suffix}"
    
    hr = HistoricalRecords(custom_model_name=name_function)
    hr.module = 'test_module'
    
    class MockMeta:
        object_name = model_name
    
    class MockModel:
        _meta = MockMeta()
        __module__ = 'test_module'
    
    expected = f"{prefix}{model_name}{suffix}"
    
    # Check if the result would conflict with the original model
    if expected.lower() == model_name.lower():
        try:
            history_name = hr.get_history_model_name(MockModel)
            assert False, f"Should have raised ValueError for conflicting name"
        except ValueError as e:
            assert "same as the model it is tracking" in str(e)
    else:
        history_name = hr.get_history_model_name(MockModel)
        assert history_name == expected


# Test 7: HistoricalQuerySet latest_of_each filtering
@given(
    num_records=st.integers(min_value=1, max_value=10)
)
def test_historical_queryset_latest_of_each(num_records):
    """Test that latest_of_each returns the correct number of records"""
    
    # This is a conceptual test since we can't easily create actual records
    # But we can test the method doesn't crash with various inputs
    
    class MockModel:
        class _meta:
            class pk:
                attname = "id"
    
    class MockHistoricalModel(models.Model):
        class Meta:
            app_label = 'test'
            abstract = True
        
        instance_type = MockModel
        history_date = models.DateTimeField()
        history_type = models.CharField(max_length=1)
    
    qs = HistoricalQuerySet(model=MockHistoricalModel)
    
    # This should not raise an error
    latest_qs = qs.latest_of_each()
    
    # Verify the queryset still has the correct attributes
    assert hasattr(latest_qs, '_pk_attr')
    assert latest_qs._pk_attr == 'id'


# Test 8: Field exclusion with None vs empty list
@given(
    use_none=st.booleans()
)
def test_excluded_fields_none_vs_empty(use_none):
    """Test that None and [] are handled differently for excluded_fields"""
    
    if use_none:
        hr = HistoricalRecords(excluded_fields=None)
        assert hr.excluded_fields == []
        assert isinstance(hr.excluded_fields, list)
    else:
        hr = HistoricalRecords(excluded_fields=[])
        assert hr.excluded_fields == []
        assert isinstance(hr.excluded_fields, list)
    
    # Both should result in empty list
    hr_none = HistoricalRecords(excluded_fields=None)
    hr_empty = HistoricalRecords(excluded_fields=[])
    assert hr_none.excluded_fields == hr_empty.excluded_fields


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])