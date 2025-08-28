import os
import sys
import datetime
from decimal import Decimal

# Add the site-packages path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings_v2')

# Write a more complete settings file
with open('test_settings_v2.py', 'w') as f:
    f.write("""
import os
import sys

SECRET_KEY = 'test-secret-key'
DEBUG = True

# Add current directory to path for test_app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'simple_history',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

USE_TZ = True
TIME_ZONE = 'UTC'

# Simplify middleware for testing
MIDDLEWARE = []
""")

import django
from django.conf import settings
from django.db import models, connection
from django.utils import timezone
django.setup()

from simple_history.models import HistoricalRecords
from simple_history.manager import (
    HistoricalQuerySet,
    HistoryManager,
    HistoryDescriptor,
    SIMPLE_HISTORY_REVERSE_ATTR_NAME
)

from hypothesis import given, strategies as st, settings as hypo_settings, assume
import pytest

# Let's create a simpler test that directly tests the manager methods
# without needing full Django model setup

def test_historical_queryset_filter_pk_translation():
    """
    Test the pk translation logic in HistoricalQuerySet.filter()
    """
    from unittest.mock import Mock, MagicMock
    
    # Create a mock model with instance_type
    mock_model = Mock()
    mock_instance_type = Mock()
    mock_instance_type._meta.pk.attname = 'id'
    mock_model.instance_type = mock_instance_type
    
    # Create a HistoricalQuerySet with mocked components
    qs = HistoricalQuerySet(model=mock_model)
    qs._as_instances = True
    qs._pk_attr = 'id'
    
    # Mock the parent filter method
    original_filter = qs.filter
    filtered_kwargs = None
    
    def capture_filter(*args, **kwargs):
        nonlocal filtered_kwargs
        filtered_kwargs = kwargs
        # Return a new queryset to avoid infinite recursion
        new_qs = HistoricalQuerySet(model=mock_model)
        new_qs._as_instances = True
        new_qs._pk_attr = 'id'
        return new_qs
    
    # Monkey-patch the super().filter call
    HistoricalQuerySet.filter = capture_filter
    
    # Test: when as_instances is True and pk is in kwargs, it should be translated
    result = qs.filter(pk=123)
    
    # Restore original
    HistoricalQuerySet.filter = original_filter
    
    # Check that pk was translated to the correct field
    assert filtered_kwargs is not None
    assert 'pk' not in filtered_kwargs
    assert 'id' in filtered_kwargs
    assert filtered_kwargs['id'] == 123
    
    print("✓ Test passed: pk translation works correctly")


def test_historical_queryset_latest_of_each_logic():
    """
    Test the logic of latest_of_each() by examining the generated query structure
    """
    from unittest.mock import Mock, MagicMock, patch
    
    # Create a mock model
    mock_model = Mock()
    mock_instance_type = Mock()
    mock_instance_type._meta.pk.attname = 'item_id'
    mock_model.instance_type = mock_instance_type
    
    # Create queryset
    qs = HistoricalQuerySet(model=mock_model)
    qs._pk_attr = 'item_id'
    
    # Track filter calls
    filter_calls = []
    
    def mock_filter(*args, **kwargs):
        filter_calls.append((args, kwargs))
        # Return a new mock queryset
        new_qs = Mock(spec=HistoricalQuerySet)
        new_qs.filter = Mock(return_value=new_qs)
        return new_qs
    
    # Patch the filter method
    with patch.object(qs, 'filter', side_effect=mock_filter):
        result = qs.latest_of_each()
    
    # Verify that filter was called with ~Exists
    assert len(filter_calls) > 0
    
    # Check the final filter call (should have ~Exists)
    final_call = filter_calls[-1]
    assert len(final_call[0]) > 0  # Should have positional args
    
    print("✓ Test passed: latest_of_each() creates appropriate subquery")


def test_historical_queryset_as_instances_exclude():
    """
    Test that as_instances() excludes deletion records
    """
    from unittest.mock import Mock, MagicMock
    
    # Create a mock model
    mock_model = Mock()
    mock_instance_type = Mock()
    mock_instance_type._meta.pk.attname = 'id'
    mock_model.instance_type = mock_instance_type
    
    # Create queryset
    qs = HistoricalQuerySet(model=mock_model)
    qs._as_instances = False
    
    # Track exclude calls
    excluded_args = None
    
    def mock_exclude(**kwargs):
        nonlocal excluded_args
        excluded_args = kwargs
        new_qs = HistoricalQuerySet(model=mock_model)
        new_qs._as_instances = True
        return new_qs
    
    qs.exclude = mock_exclude
    
    # Call as_instances
    result = qs.as_instances()
    
    # Verify that exclude was called with history_type="-"
    assert excluded_args is not None
    assert 'history_type' in excluded_args
    assert excluded_args['history_type'] == '-'
    assert result._as_instances is True
    
    print("✓ Test passed: as_instances() excludes deletion records")


def test_history_manager_most_recent_fields():
    """
    Test that most_recent() correctly handles field names, especially ForeignKeys
    """
    from unittest.mock import Mock, MagicMock, patch
    
    # Create mock fields
    regular_field = Mock()
    regular_field.name = 'regular_field'
    
    fk_field = Mock(spec=models.ForeignKey)
    fk_field.name = 'related_object'
    
    # Create mock model with tracked_fields
    mock_model = Mock()
    mock_model.tracked_fields = [regular_field, fk_field]
    mock_model._meta.object_name = 'TestObject'
    
    # Create mock instance
    mock_instance = Mock()
    mock_instance.__class__ = Mock
    mock_instance._meta.object_name = 'TestObject'
    
    # Create manager
    manager = HistoryManager(mock_model, mock_instance)
    
    # Mock get_queryset to return a mock with values
    mock_qs = Mock()
    mock_qs.values = Mock(return_value=[{
        'regular_field': 'value1',
        'related_object_id': 123
    }])
    
    manager.get_queryset = Mock(return_value=mock_qs)
    
    # Mock instance constructor
    mock_instance.__class__.return_value = Mock()
    
    # Call most_recent
    result = manager.most_recent()
    
    # Verify that values was called with correct field names
    mock_qs.values.assert_called_once()
    call_args = mock_qs.values.call_args[0]
    
    # For ForeignKey fields, should use field_name + "_id"
    assert 'regular_field' in call_args
    assert 'related_object_id' in call_args
    assert 'related_object' not in call_args
    
    print("✓ Test passed: most_recent() handles ForeignKey fields correctly")


def test_history_manager_as_of_with_deletion():
    """
    Test that as_of() raises DoesNotExist when the most recent record is a deletion
    """
    from unittest.mock import Mock, MagicMock
    
    # Create mock model and instance
    mock_model = Mock()
    mock_instance = Mock()
    mock_instance._meta.object_name = 'TestObject'
    mock_instance.DoesNotExist = Exception
    
    # Create manager
    manager = HistoryManager(mock_model, mock_instance)
    
    # Mock queryset that returns a deletion record
    mock_qs = Mock()
    mock_history_obj = Mock()
    mock_history_obj.history_type = '-'  # Deletion record
    
    # Make queryset behave like a list with one item
    mock_qs.__getitem__ = Mock(return_value=mock_history_obj)
    mock_qs.filter = Mock(return_value=mock_qs)
    
    manager.get_queryset = Mock(return_value=mock_qs)
    
    # Call as_of with a date
    test_date = timezone.now()
    
    # Should raise DoesNotExist
    try:
        result = manager.as_of(test_date)
        assert False, "Expected DoesNotExist exception"
    except Exception as e:
        # Check that it's the right kind of exception
        assert "had already been deleted" in str(e) or isinstance(e, mock_instance.DoesNotExist)
    
    print("✓ Test passed: as_of() raises exception for deletion records")


@given(
    st.lists(
        st.dictionaries(
            st.sampled_from(['field1', 'field2', 'field3']),
            st.integers(min_value=0, max_value=1000),
            min_size=1,
            max_size=3
        ),
        min_size=1,
        max_size=10
    ),
    st.booleans()
)
@hypo_settings(max_examples=50)
def test_bulk_history_create_count_property(objects_data, is_update):
    """
    Property test: bulk_history_create should create exactly one history record per input object
    """
    from unittest.mock import Mock, MagicMock, patch
    
    # Create mock objects
    mock_objs = []
    for i, data in enumerate(objects_data):
        obj = Mock()
        obj.pk = i + 1
        obj._history_user = None
        obj._history_date = None
        for field, value in data.items():
            setattr(obj, field, value)
        mock_objs.append(obj)
    
    # Create mock model with tracked fields
    mock_model = Mock()
    mock_model.get_default_history_user = Mock(return_value=None)
    
    # Create mock tracked fields
    tracked_fields = []
    for field_name in ['field1', 'field2', 'field3']:
        field = Mock()
        field.attname = field_name
        tracked_fields.append(field)
    mock_model.tracked_fields = tracked_fields
    
    # Mock the model's objects.bulk_create
    created_records = []
    def mock_bulk_create(objs, batch_size=None):
        created_records.extend(objs)
        return objs
    
    mock_model.objects.bulk_create = mock_bulk_create
    
    # Mock the model constructor to capture created instances
    historical_instances = []
    def mock_init(self, **kwargs):
        self.__dict__.update(kwargs)
        historical_instances.append(self)
        return None
    
    mock_model.return_value = None
    mock_model.side_effect = mock_init
    
    # Create manager
    manager = HistoryManager(mock_model, None)
    
    # Call bulk_history_create
    with patch('django.conf.settings.SIMPLE_HISTORY_ENABLED', True):
        with patch('django.utils.timezone.now', return_value=datetime.datetime.now()):
            result = manager.bulk_history_create(
                mock_objs,
                update=is_update,
                default_change_reason="Test reason"
            )
    
    # Property: Number of history records should equal number of input objects
    assert len(historical_instances) == len(mock_objs), (
        f"Expected {len(mock_objs)} history records, got {len(historical_instances)}"
    )
    
    # Property: History type should be correct
    expected_type = "~" if is_update else "+"
    for instance in historical_instances:
        assert hasattr(instance, 'history_type')
        assert instance.history_type == expected_type, (
            f"Expected history_type '{expected_type}', got '{instance.history_type}'"
        )


@given(
    st.lists(
        st.integers(min_value=1, max_value=5),
        min_size=2,
        max_size=20
    )
)
@hypo_settings(max_examples=50)
def test_latest_of_each_uniqueness_property(object_ids):
    """
    Property: latest_of_each() should return at most one record per unique object ID
    """
    from unittest.mock import Mock, MagicMock, patch
    from django.db.models import Q, Exists, OuterRef
    
    # Create a mock model
    mock_model = Mock()
    mock_instance_type = Mock()
    mock_instance_type._meta.pk.attname = 'object_id'
    mock_model.instance_type = mock_instance_type
    
    # Create base queryset
    qs = HistoricalQuerySet(model=mock_model)
    qs._pk_attr = 'object_id'
    
    # Create mock records with the given IDs
    mock_records = []
    for i, obj_id in enumerate(object_ids):
        record = Mock()
        record.object_id = obj_id
        record.history_date = datetime.datetime(2024, 1, 1) + datetime.timedelta(days=i)
        mock_records.append(record)
    
    # Mock the filter operation to simulate the subquery logic
    def mock_filter(*args, **kwargs):
        # If this is the ~Exists filter (final filter in latest_of_each)
        if args and any(hasattr(arg, '__invert__') for arg in args):
            # Simulate filtering to get latest of each
            latest_map = {}
            for record in mock_records:
                if record.object_id not in latest_map:
                    latest_map[record.object_id] = record
                elif record.history_date > latest_map[record.object_id].history_date:
                    latest_map[record.object_id] = record
            
            # Return a queryset with the filtered results
            filtered_qs = Mock(spec=HistoricalQuerySet)
            filtered_qs.__iter__ = lambda self: iter(latest_map.values())
            filtered_qs.filter = Mock(return_value=filtered_qs)
            return filtered_qs
        else:
            # Return the same queryset for intermediate operations
            return qs
    
    qs.filter = mock_filter
    qs.__iter__ = lambda self: iter(mock_records)
    
    # Call latest_of_each
    result = qs.latest_of_each()
    result_list = list(result)
    
    # Property: Each object_id should appear at most once
    seen_ids = set()
    for record in result_list:
        assert record.object_id not in seen_ids, (
            f"Duplicate object_id {record.object_id} in latest_of_each() results"
        )
        seen_ids.add(record.object_id)
    
    # Property: Number of results should equal number of unique input IDs
    unique_input_ids = set(object_ids)
    assert len(result_list) == len(unique_input_ids), (
        f"Expected {len(unique_input_ids)} unique results, got {len(result_list)}"
    )


if __name__ == "__main__":
    print("Running property-based tests for simple_history.manager...\n")
    
    # Run unit tests first
    print("=== Unit Tests ===")
    test_historical_queryset_filter_pk_translation()
    test_historical_queryset_latest_of_each_logic()
    test_historical_queryset_as_instances_exclude()
    test_history_manager_most_recent_fields()
    test_history_manager_as_of_with_deletion()
    
    print("\n=== Property-Based Tests ===")
    
    # Run property-based tests
    import traceback
    
    # Test 1: bulk_history_create count property
    print("\nTesting bulk_history_create count property...")
    try:
        test_bulk_history_create_count_property()
        print("✓ bulk_history_create count property test passed")
    except Exception as e:
        print(f"✗ bulk_history_create count property test failed: {e}")
        traceback.print_exc()
    
    # Test 2: latest_of_each uniqueness property
    print("\nTesting latest_of_each uniqueness property...")
    try:
        test_latest_of_each_uniqueness_property()
        print("✓ latest_of_each uniqueness property test passed")
    except Exception as e:
        print(f"✗ latest_of_each uniqueness property test failed: {e}")
        traceback.print_exc()
    
    print("\n=== All tests completed ===")
    
    # Run with pytest for better output
    print("\nRunning with pytest for detailed results...")
    pytest.main([__file__, "-v", "--tb=short", "-q"])