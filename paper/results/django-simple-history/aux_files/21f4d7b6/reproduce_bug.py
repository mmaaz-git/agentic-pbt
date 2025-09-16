"""Minimal reproducer for the excluded_fields bug in clean_duplicate_history."""

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


def reproduce_bug():
    """Reproduce the AttributeError with excluded_fields."""
    print("Reproducing bug: Command object missing excluded_fields attribute")
    print("-" * 60)
    
    # Create a Command instance
    cmd = Command()
    
    # Create mock history entries
    entry1 = Mock()
    entry2 = Mock()
    
    # Mock diff_against to return no changes (duplicate entries)
    mock_delta = Mock()
    mock_delta.changed_fields = []
    entry1.diff_against.return_value = mock_delta
    
    # Try to call _check_and_delete without initializing excluded_fields
    # This should fail with AttributeError
    try:
        result = cmd._check_and_delete(entry1, entry2, dry_run=True)
        print(f"Result: {result}")
    except AttributeError as e:
        print(f"ERROR: {e}")
        print("\nThe bug is confirmed!")
        print("\nExplanation:")
        print("The _check_and_delete method assumes self.excluded_fields exists,")
        print("but this attribute is only set in the handle() method when the command")
        print("is run through Django's management interface.")
        print("\nWhen the method is called directly (e.g., in unit tests),")
        print("the attribute doesn't exist and causes an AttributeError.")
        return True
    
    print("No error occurred - unexpected!")
    return False


if __name__ == "__main__":
    if reproduce_bug():
        print("\n" + "="*60)
        print("BUG CONFIRMED: AttributeError when calling _check_and_delete directly")
        print("="*60)