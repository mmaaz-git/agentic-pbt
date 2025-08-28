import os
import sys

# Add the site-packages path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings_v2')

import django
django.setup()

from simple_history.manager import HistoricalQuerySet
from unittest.mock import Mock, MagicMock
from django.db import models

def test_filter_pk_translation_bug():
    """
    Reproduce the bug in HistoricalQuerySet.filter() where pk is not translated
    when _as_instances is True.
    """
    
    # Create a mock model with instance_type
    mock_model = Mock()
    mock_instance_type = Mock()
    mock_instance_type._meta.pk.attname = 'id'
    mock_model.instance_type = mock_instance_type
    
    # Create a HistoricalQuerySet
    qs = HistoricalQuerySet(model=mock_model)
    qs._as_instances = True
    qs._pk_attr = 'id'
    
    # Capture what gets passed to the parent filter
    captured_args = None
    captured_kwargs = None
    original_filter = models.QuerySet.filter
    
    def capture_filter(self, *args, **kwargs):
        nonlocal captured_args, captured_kwargs
        captured_args = args
        captured_kwargs = kwargs
        # Call the original to avoid breaking things
        return original_filter(self, *args, **kwargs)
    
    # Patch the parent class filter
    models.QuerySet.filter = capture_filter
    
    try:
        # Call filter with pk argument
        qs.filter(pk=123)
    except Exception as e:
        # Expected - we're using mocks
        pass
    finally:
        # Restore original
        models.QuerySet.filter = original_filter
    
    print("Test Results:")
    print(f"  _as_instances: {qs._as_instances}")
    print(f"  _pk_attr: {qs._pk_attr}")
    print(f"  Captured kwargs: {captured_kwargs}")
    print()
    
    # Check if pk was translated
    if captured_kwargs:
        if 'pk' in captured_kwargs:
            print("❌ BUG CONFIRMED: 'pk' was NOT translated to 'id'")
            print("   Expected: {'id': 123}")
            print(f"   Got: {captured_kwargs}")
            return False
        elif 'id' in captured_kwargs and captured_kwargs['id'] == 123:
            print("✓ PASS: 'pk' was correctly translated to 'id'")
            return True
    else:
        print("⚠ Warning: Could not capture filter arguments")
        return None

def verify_implementation():
    """
    Check the actual implementation in the source code
    """
    print("\n=== Checking Implementation ===")
    
    # Read the filter method implementation
    import inspect
    source = inspect.getsource(HistoricalQuerySet.filter)
    
    print("Source code of HistoricalQuerySet.filter:")
    print("-" * 50)
    print(source)
    print("-" * 50)
    
    # Check the logic
    if 'kwargs.pop("pk")' in source:
        print("✓ Implementation appears to modify kwargs['pk']")
        print("  Found: kwargs.pop('pk') statement")
    else:
        print("⚠ Implementation may not be modifying kwargs correctly")

def test_super_call_issue():
    """
    Test if the issue is with how super().filter() is called
    """
    print("\n=== Testing super() call behavior ===")
    
    class Parent:
        def filter(self, *args, **kwargs):
            print(f"  Parent.filter called with kwargs: {kwargs}")
            return self
    
    class Child(Parent):
        def filter(self, *args, **kwargs):
            print(f"  Child.filter called with kwargs: {kwargs}")
            if "pk" in kwargs:
                kwargs["id"] = kwargs.pop("pk")
                print(f"  Child.filter modified kwargs to: {kwargs}")
            return super().filter(*args, **kwargs)
    
    obj = Child()
    print("Calling child.filter(pk=123):")
    obj.filter(pk=123)
    
    print("\nThis shows that the implementation SHOULD work correctly.")
    print("The bug might be in how the QuerySet inheritance chain works.")

def test_queryset_inheritance():
    """
    Test the actual QuerySet inheritance to understand the bug
    """
    print("\n=== Testing QuerySet Inheritance ===")
    
    from django.db.models import QuerySet
    
    # Check the MRO (Method Resolution Order)
    print("HistoricalQuerySet MRO:")
    for i, cls in enumerate(HistoricalQuerySet.__mro__):
        print(f"  {i}: {cls}")
    
    # Check if filter is overridden correctly
    print(f"\nHistoricalQuerySet has its own filter? {hasattr(HistoricalQuerySet, 'filter')}")
    print(f"Is it the same as QuerySet.filter? {HistoricalQuerySet.filter == QuerySet.filter}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing HistoricalQuerySet.filter() pk translation bug")
    print("=" * 60)
    
    # Run tests
    result = test_filter_pk_translation_bug()
    verify_implementation()
    test_super_call_issue()
    test_queryset_inheritance()
    
    if result is False:
        print("\n" + "=" * 60)
        print("BUG CONFIRMED: HistoricalQuerySet.filter() does not correctly")
        print("translate 'pk' to the model's primary key field when")
        print("_as_instances is True.")
        print("=" * 60)