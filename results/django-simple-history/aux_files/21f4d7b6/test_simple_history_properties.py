"""Property-based tests for simple_history.management commands."""

import sys
import os
import datetime
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add django-simple-history env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

# Configure Django settings before importing
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'

import django
from django.conf import settings
from django.apps import apps

# Configure minimal Django settings
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
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'simple_history',
        ],
        USE_TZ=True,
        SECRET_KEY='test-secret-key',
    )
    django.setup()

from hypothesis import given, strategies as st, assume, settings as hypo_settings
from simple_history.management.commands import populate_history, clean_old_history, clean_duplicate_history
from django.utils import timezone
import math


# Test 1: Natural key parsing in populate_history
@given(
    app_label=st.text(min_size=1, max_size=50).filter(lambda x: '.' not in x and ' ' not in x),
    model_name=st.text(min_size=1, max_size=50).filter(lambda x: '.' not in x and ' ' not in x)
)
def test_model_from_natural_key_parsing(app_label, model_name):
    """Test that _model_from_natural_key correctly parses app.model format."""
    cmd = populate_history.Command()
    natural_key = f"{app_label}.{model_name}"
    
    # Mock get_model to avoid actual model lookup
    with patch('simple_history.management.commands.populate_history.get_model') as mock_get_model:
        # Mock the model to raise LookupError (model not found)
        mock_get_model.side_effect = LookupError()
        
        try:
            model, history = cmd._model_from_natural_key(natural_key)
        except ValueError as e:
            # Should only fail with MODEL_NOT_FOUND message
            assert cmd.MODEL_NOT_FOUND in str(e)
            # The error message should contain the natural_key
            assert natural_key in str(e)
            
            # Verify get_model was called with correct arguments
            mock_get_model.assert_called_once_with(app_label, model_name)


# Test 2: Invalid natural key format handling
@given(
    invalid_key=st.text(min_size=1, max_size=100).filter(lambda x: '.' not in x)
)
def test_model_from_natural_key_invalid_format(invalid_key):
    """Test that _model_from_natural_key handles invalid format correctly."""
    cmd = populate_history.Command()
    
    with patch('simple_history.management.commands.populate_history.get_model') as mock_get_model:
        try:
            model, history = cmd._model_from_natural_key(invalid_key)
        except ValueError as e:
            # Should fail with MODEL_NOT_FOUND message for invalid format
            assert cmd.MODEL_NOT_FOUND in str(e)
            assert invalid_key in str(e)


# Test 3: Date calculation precision in clean_old_history
@given(
    days=st.integers(min_value=1, max_value=365*10)  # Up to 10 years
)
@hypo_settings(deadline=None)
def test_clean_old_history_date_calculation(days):
    """Test that date calculation is exact with timedelta."""
    cmd = clean_old_history.Command()
    
    # Mock timezone.now() to get a fixed time
    fixed_now = timezone.now()
    with patch('simple_history.management.commands.clean_old_history.timezone.now', return_value=fixed_now):
        # Create mock model and history_model
        mock_model = Mock()
        mock_history_model = Mock()
        mock_history_model.objects.filter.return_value.count.return_value = 0
        
        # Call _process with our days value
        cmd.verbosity = 0  # Suppress output
        cmd._process([(mock_model, mock_history_model)], days_back=days, dry_run=True)
        
        # Verify the filter was called with correct date
        expected_date = fixed_now - timezone.timedelta(days=days)
        mock_history_model.objects.filter.assert_called_once()
        
        # Extract the actual filter argument
        call_args = mock_history_model.objects.filter.call_args
        
        # Check that history_date__lt was used with the correct date
        if call_args[1]:  # kwargs
            actual_date = call_args[1].get('history_date__lt')
        else:  # positional args
            actual_date = call_args[0].get('history_date__lt')
        
        # The dates should be exactly equal
        assert actual_date == expected_date


# Test 4: Dry run should never delete in clean_duplicate_history  
@given(
    dry_run=st.booleans()
)
def test_check_and_delete_dry_run_behavior(dry_run):
    """Test that _check_and_delete respects dry_run flag."""
    cmd = clean_duplicate_history.Command()
    
    # Create mock history entries
    entry1 = Mock()
    entry2 = Mock()
    
    # Mock diff_against to return no changes (duplicate entries)
    mock_delta = Mock()
    mock_delta.changed_fields = []  # No changes means they're duplicates
    entry1.diff_against.return_value = mock_delta
    
    # Call _check_and_delete
    result = cmd._check_and_delete(entry1, entry2, dry_run=dry_run)
    
    # Should return 1 when entries are duplicates
    assert result == 1
    
    # Check if delete was called based on dry_run
    if dry_run:
        entry1.delete.assert_not_called()
    else:
        entry1.delete.assert_called_once()


# Test 5: Batch size handling in populate_history
@given(
    batch_size=st.integers(min_value=1, max_value=1000),
    num_instances=st.integers(min_value=0, max_value=1000)
)
@hypo_settings(deadline=None)
def test_bulk_history_create_batch_handling(batch_size, num_instances):
    """Test that bulk_history_create handles all instances regardless of batch_size."""
    cmd = populate_history.Command()
    cmd.verbosity = 0  # Suppress output
    cmd.stdout = StringIO()  # Capture output
    
    # Create mock model and instances
    mock_model = Mock()
    mock_model._default_manager.iterator.return_value = iter(range(num_instances))
    
    # Mock history manager
    mock_history = Mock()
    mock_history.bulk_history_create = Mock()
    
    with patch('simple_history.management.commands.populate_history.utils.get_history_manager_for_model', 
               return_value=mock_history):
        cmd._bulk_history_create(mock_model, batch_size)
        
        # Calculate expected number of bulk_history_create calls
        if num_instances == 0:
            expected_calls = 0
        else:
            # One call per full batch, plus one for remainder if any
            expected_calls = math.ceil(num_instances / batch_size)
        
        actual_calls = mock_history.bulk_history_create.call_count
        assert actual_calls == expected_calls
        
        # Verify total number of instances processed
        if num_instances > 0:
            total_processed = 0
            for call in mock_history.bulk_history_create.call_args_list:
                instances_in_call = len(call[0][0])  # First positional arg is the list of instances
                total_processed += instances_in_call
            
            assert total_processed == num_instances


# Test 6: Edge case with minutes parameter in clean_duplicate_history
@given(
    minutes=st.integers(min_value=0, max_value=60*24*365)  # Up to 1 year in minutes
)
@hypo_settings(deadline=None)
def test_clean_duplicate_history_minutes_calculation(minutes):
    """Test that minutes parameter correctly calculates stop_date."""
    cmd = clean_duplicate_history.Command()
    
    # Mock timezone.now() to get a fixed time
    fixed_now = timezone.now()
    with patch('simple_history.management.commands.clean_duplicate_history.timezone.now', return_value=fixed_now):
        # Create mock model and history_model
        mock_model = Mock()
        mock_model._meta.pk.name = 'id'
        mock_model._default_manager.all.return_value.iterator.return_value = iter([])
        
        mock_history_model = Mock()
        mock_history_model.objects.filter.return_value.count.return_value = 0
        mock_history_model.objects.filter.return_value.exists.return_value = False
        
        # Call _process with our minutes value
        cmd.verbosity = 0  # Suppress output
        cmd._process([(mock_model, mock_history_model)], date_back=minutes, dry_run=True)
        
        if minutes:
            # Calculate expected stop_date
            expected_stop_date = fixed_now - timezone.timedelta(minutes=minutes)
            
            # Verify the filter was called with correct date
            mock_history_model.objects.filter.assert_called()
            call_args = mock_history_model.objects.filter.call_args
            
            # Check that history_date__gte was used with the correct date
            if call_args[1]:  # kwargs
                actual_date = call_args[1].get('history_date__gte')
            else:  # positional args
                actual_date = call_args[0].get('history_date__gte') if call_args[0] else None
            
            assert actual_date == expected_stop_date


if __name__ == "__main__":
    print("Running property-based tests for simple_history.management...")
    
    # Run the tests
    test_model_from_natural_key_parsing()
    print("✓ Natural key parsing test passed")
    
    test_model_from_natural_key_invalid_format()
    print("✓ Invalid natural key format test passed")
    
    test_clean_old_history_date_calculation()
    print("✓ Date calculation test passed")
    
    test_check_and_delete_dry_run_behavior()
    print("✓ Dry run behavior test passed")
    
    test_bulk_history_create_batch_handling()
    print("✓ Batch handling test passed")
    
    test_clean_duplicate_history_minutes_calculation()
    print("✓ Minutes calculation test passed")
    
    print("\nAll tests passed!")