import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

import simple_history.utils as utils
from unittest.mock import Mock
from django.db.models import ForeignKey

def test_get_history_manager_crash():
    """
    Test if get_history_manager_from_history crashes when the model
    has a ForeignKey primary key with None name
    """
    # Create a mock history instance
    history_instance = Mock()
    
    # Create a mock model with ForeignKey pk that has None name
    mock_model = Mock()
    mock_pk = Mock(spec=ForeignKey)
    mock_pk.name = None  # This causes the bug
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    mock_model._meta.simple_history_manager_attribute = "history"
    
    # Set up the instance_type to return our buggy model
    history_instance.instance_type = mock_model
    
    # This should crash when it calls get_app_model_primary_key_name internally
    try:
        result = utils.get_history_manager_from_history(history_instance)
        print("ERROR: Should have crashed but didn't")
        return False
    except TypeError as e:
        print(f"✓ Confirmed crash in get_history_manager_from_history: {e}")
        return True
    except AttributeError as e:
        # Might fail earlier due to mock setup
        print(f"Mock setup issue: {e}")
        return False

def test_update_change_reason_crash():
    """
    Test if update_change_reason crashes when model has ForeignKey pk with None name
    """
    # Create instance with ForeignKey pk that has None name  
    instance = Mock()
    instance.pk = 1
    
    mock_model = Mock()
    mock_pk = Mock(spec=ForeignKey)
    mock_pk.name = None  # This causes the bug
    mock_model._meta = Mock()
    mock_model._meta.pk = mock_pk
    mock_model._meta.simple_history_manager_attribute = "history"
    
    # Make type(instance) return our mock model
    instance.__class__ = mock_model
    instance._meta = mock_model._meta
    
    # Try to update change reason - this might crash
    try:
        utils.update_change_reason(instance, "test reason")
        print("ERROR: Should have crashed but didn't")
        return False
    except TypeError as e:
        if "NoneType" in str(e):
            print(f"✓ Confirmed crash in update_change_reason: {e}")
            return True
        else:
            print(f"Different error: {e}")
            return False
    except Exception as e:
        print(f"Other exception: {e}")
        return False

if __name__ == "__main__":
    print("Testing cascade effects of the None name bug:\n")
    
    bug1 = test_get_history_manager_crash()
    bug2 = test_update_change_reason_crash()
    
    if bug1 or bug2:
        print("\n🐛 BUG IMPACT: The None name bug affects multiple functions in the utils module")
        print("Any function that calls get_app_model_primary_key_name can crash with TypeError")