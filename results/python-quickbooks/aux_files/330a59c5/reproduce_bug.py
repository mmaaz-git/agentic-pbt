import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from datetime import datetime
from unittest.mock import Mock
from quickbooks.cdc import change_data_capture


class MockQBOClass:
    qbo_object_name = "Account"
    
    @classmethod
    def from_json(cls, data):
        return cls()


def reproduce_empty_cdc_response_bug():
    """Reproduce the IndexError when CDCResponse is empty"""
    print("Testing empty CDCResponse list bug...")
    
    mock_qb = Mock()
    mock_qb.change_data_capture = Mock(return_value={
        'CDCResponse': []  # Empty list causes IndexError
    })
    
    try:
        result = change_data_capture([MockQBOClass], datetime.now(), qb=mock_qb)
        print("ERROR: Should have raised IndexError but didn't!")
    except IndexError as e:
        print(f"✓ Bug confirmed: IndexError raised - {e}")
        print("  Line 26: cdc_response_dict[0]['QueryResponse'] assumes list has at least one element")


def reproduce_missing_query_response_bug():
    """Reproduce the KeyError when QueryResponse key is missing"""
    print("\nTesting missing QueryResponse key bug...")
    
    mock_qb = Mock()
    mock_qb.change_data_capture = Mock(return_value={
        'CDCResponse': [{
            'SomeOtherKey': 'value'  # Missing 'QueryResponse' causes KeyError
        }]
    })
    
    try:
        result = change_data_capture([MockQBOClass], datetime.now(), qb=mock_qb)
        print("ERROR: Should have raised KeyError but didn't!")
    except KeyError as e:
        print(f"✓ Bug confirmed: KeyError raised - {e}")
        print("  Line 26: assumes 'QueryResponse' key exists in response")


if __name__ == "__main__":
    reproduce_empty_cdc_response_bug()
    reproduce_missing_query_response_bug()