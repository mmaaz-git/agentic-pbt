"""Test for missing attributes in clean_duplicate_history Command."""

import sys
import os
from unittest.mock import Mock

# Add django-simple-history env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

# Configure Django settings before importing
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'

import django
from django.conf import settings

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

from simple_history.management.commands.clean_duplicate_history import Command


def test_base_manager_attribute():
    """Test that _process uses self.base_manager which may not be initialized."""
    print("Testing base_manager attribute...")
    
    cmd = Command()
    cmd.verbosity = 0  # This is set, but not base_manager
    
    # Create mock model and history_model
    mock_model = Mock()
    mock_model._meta.pk.name = 'id'
    mock_model._base_manager.all.return_value.iterator.return_value = iter([])
    mock_model._default_manager.all.return_value.iterator.return_value = iter([])
    
    mock_history_model = Mock()
    mock_history_model.objects.filter.return_value.count.return_value = 0
    mock_history_model.objects.filter.return_value.exists.return_value = False
    
    try:
        # This should access self.base_manager at line 84
        cmd._process([(mock_model, mock_history_model)], date_back=None, dry_run=True)
        print("  ✓ No error with base_manager")
        return False
    except AttributeError as e:
        print(f"  ✗ AttributeError: {e}")
        return True


def test_excluded_fields_attribute():
    """Test that _check_and_delete uses self.excluded_fields which may not be initialized."""
    print("Testing excluded_fields attribute...")
    
    cmd = Command()
    
    # Create mock history entries
    entry1 = Mock()
    entry2 = Mock()
    
    # Mock diff_against to return no changes
    mock_delta = Mock()
    mock_delta.changed_fields = []
    entry1.diff_against.return_value = mock_delta
    
    try:
        # This should access self.excluded_fields at line 130
        result = cmd._check_and_delete(entry1, entry2, dry_run=True)
        print("  ✓ No error with excluded_fields")
        return False
    except AttributeError as e:
        print(f"  ✗ AttributeError: {e}")
        return True


if __name__ == "__main__":
    print("Testing for missing attributes in clean_duplicate_history Command")
    print("="*60)
    
    bugs_found = []
    
    if test_base_manager_attribute():
        bugs_found.append("base_manager")
    
    if test_excluded_fields_attribute():
        bugs_found.append("excluded_fields")
    
    print("\n" + "="*60)
    if bugs_found:
        print(f"BUGS FOUND: Missing attributes: {', '.join(bugs_found)}")
        print("\nThese attributes are only initialized in handle() but used in other methods.")
        print("This causes AttributeError when methods are called directly.")
    else:
        print("No bugs found - all attributes properly initialized")