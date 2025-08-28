import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

import simple_history.utils as utils
from unittest.mock import Mock
from django.db.models import ForeignKey

def test_double_id_suffix():
    """
    Test what happens when a ForeignKey already has a name ending in '_id'
    This creates 'field_id_id' which might be unintended
    """
    test_cases = [
        ("user_id", "user_id_id"),
        ("post_id", "post_id_id"),
        ("author_id", "author_id_id"),
        ("id", "id_id"),
    ]
    
    for input_name, expected_output in test_cases:
        mock_model = Mock()
        mock_pk = Mock(spec=ForeignKey)
        mock_pk.name = input_name
        mock_model._meta = Mock()
        mock_model._meta.pk = mock_pk
        
        result = utils.get_app_model_primary_key_name(mock_model)
        print(f"Input: '{input_name}' -> Output: '{result}'")
        assert result == expected_output
        
    print("\n⚠️  DESIGN ISSUE: ForeignKey fields ending with '_id' get double suffix")
    print("This creates field names like 'user_id_id' which is likely unintended")
    print("The function should probably check if the name already ends with '_id'")

if __name__ == "__main__":
    test_double_id_suffix()