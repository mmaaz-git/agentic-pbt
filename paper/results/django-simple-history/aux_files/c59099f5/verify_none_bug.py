import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

import simple_history.utils as utils
from unittest.mock import Mock
from django.db.models import ForeignKey

# Reproduce the None + "_id" bug
def reproduce_bug():
    """
    Demonstrate that get_app_model_primary_key_name crashes when 
    a ForeignKey primary key has None as its name
    """
    mock_model = Mock()
    mock_pk = Mock(spec=ForeignKey)
    mock_pk.name = None  # This could happen if model metadata is corrupted or uninitialized
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    
    try:
        result = utils.get_app_model_primary_key_name(mock_model)
        print(f"Result: {result}")
        return False  # Should have raised TypeError
    except TypeError as e:
        print(f"TypeError raised as expected: {e}")
        return True

if __name__ == "__main__":
    bug_found = reproduce_bug()
    if bug_found:
        print("\nBUG CONFIRMED: get_app_model_primary_key_name crashes with TypeError when ForeignKey pk.name is None")
        print("This violates the principle that utility functions should handle edge cases gracefully")