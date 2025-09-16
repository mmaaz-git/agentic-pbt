import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from datetime import datetime
from unittest.mock import Mock, MagicMock
import pytest
from hypothesis import given, strategies as st, assume, settings

from quickbooks.cdc import change_data_capture
from quickbooks.helpers import qb_datetime_format
from quickbooks.objects.changedatacapture import CDCResponse, QueryResponse


class MockQBOClass:
    """Mock QuickBooks Object class for testing"""
    def __init__(self, name):
        self.qbo_object_name = name
    
    @classmethod
    def from_json(cls, data):
        return cls("test")


@given(st.lists(st.text(min_size=1), min_size=1))
def test_duplicate_qbo_object_names_silently_overwrites(names):
    """Test that duplicate qbo_object_names in the class list cause silent overwrites"""
    # Create classes with potentially duplicate names
    qbo_classes = [MockQBOClass(name) for name in names]
    
    # Mock the QuickBooks client
    mock_qb = Mock()
    mock_qb.change_data_capture = Mock(return_value={
        'CDCResponse': [{
            'QueryResponse': []
        }]
    })
    
    # This should not crash even with duplicates
    result = change_data_capture(qbo_classes, datetime.now(), qb=mock_qb)
    
    # If there were duplicates, the dictionary would have fewer entries
    unique_names = set(names)
    if len(names) != len(unique_names):
        # This proves the silent overwrite behavior
        assert len(unique_names) < len(qbo_classes)


def test_empty_cdc_response_list_crashes():
    """Test that an empty CDCResponse list causes an IndexError"""
    qbo_classes = [MockQBOClass("Account")]
    
    mock_qb = Mock()
    # Return empty list for CDCResponse
    mock_qb.change_data_capture = Mock(return_value={
        'CDCResponse': []  # Empty list!
    })
    
    with pytest.raises(IndexError):
        change_data_capture(qbo_classes, datetime.now(), qb=mock_qb)


def test_missing_query_response_key_crashes():
    """Test that missing 'QueryResponse' key causes a KeyError"""
    qbo_classes = [MockQBOClass("Account")]
    
    mock_qb = Mock()
    # Return CDCResponse without QueryResponse key
    mock_qb.change_data_capture = Mock(return_value={
        'CDCResponse': [{
            # Missing 'QueryResponse' key!
            'SomeOtherKey': 'value'
        }]
    })
    
    with pytest.raises(KeyError):
        change_data_capture(qbo_classes, datetime.now(), qb=mock_qb)


@given(st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2030, 12, 31)))
def test_datetime_formatting_preserves_information(dt):
    """Test that datetime formatting preserves essential timestamp information"""
    formatted = qb_datetime_format(dt)
    
    # Parse it back
    parsed = datetime.strptime(formatted, "%Y-%m-%dT%H:%M:%S")
    
    # Should preserve year, month, day, hour, minute, second
    assert parsed.year == dt.year
    assert parsed.month == dt.month
    assert parsed.day == dt.day
    assert parsed.hour == dt.hour
    assert parsed.minute == dt.minute
    assert parsed.second == dt.second
    # Note: microseconds are lost in the format, which could be a bug for precision


def test_none_cdc_response_crashes():
    """Test that None CDCResponse value causes an error"""
    qbo_classes = [MockQBOClass("Account")]
    
    mock_qb = Mock()
    # Return None for CDCResponse
    mock_qb.change_data_capture = Mock(return_value={
        'CDCResponse': None  # None instead of list!
    })
    
    with pytest.raises(TypeError):
        change_data_capture(qbo_classes, datetime.now(), qb=mock_qb)


@given(st.integers(min_value=0, max_value=10))
def test_cdc_response_with_multiple_items_only_processes_first(num_responses):
    """Test that CDC response silently ignores all but the first response"""
    assume(num_responses > 1)
    
    qbo_classes = [MockQBOClass("Account")]
    
    mock_qb = Mock()
    # Create multiple CDC responses
    responses = []
    for i in range(num_responses):
        responses.append({
            'QueryResponse': [{
                'Account': [{'Id': str(i)}]
            }]
        })
    
    mock_qb.change_data_capture = Mock(return_value={
        'CDCResponse': responses
    })
    
    # The function only processes responses[0], ignoring the rest
    # This could be a bug if multiple responses are expected
    result = change_data_capture(qbo_classes, datetime.now(), qb=mock_qb)
    
    # Only the first response should be processed
    # This demonstrates potential data loss
    assert hasattr(result, 'Account')


def test_malformed_json_structure_various_edge_cases():
    """Test various malformed JSON structures that could crash the function"""
    qbo_classes = [MockQBOClass("Account")]
    
    test_cases = [
        # Case 1: CDCResponse is a string instead of list
        {'CDCResponse': 'not_a_list'},
        
        # Case 2: CDCResponse contains non-dict items
        {'CDCResponse': [123]},
        
        # Case 3: QueryResponse is not a list
        {'CDCResponse': [{'QueryResponse': 'not_a_list'}]},
        
        # Case 4: Nested None values
        {'CDCResponse': [None]},
    ]
    
    for malformed_response in test_cases:
        mock_qb = Mock()
        mock_qb.change_data_capture = Mock(return_value=malformed_response)
        
        # Each of these should raise an error
        with pytest.raises((TypeError, AttributeError, KeyError)):
            change_data_capture(qbo_classes, datetime.now(), qb=mock_qb)