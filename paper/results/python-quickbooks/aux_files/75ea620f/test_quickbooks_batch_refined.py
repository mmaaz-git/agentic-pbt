import sys
import os
import uuid
from unittest.mock import Mock, MagicMock, patch
from hypothesis import given, strategies as st, assume, settings
import json

sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.batch import BatchManager, batch_create, batch_update, batch_delete
from quickbooks.exceptions import QuickbooksException
from quickbooks.objects.batchrequest import (
    IntuitBatchRequest, BatchItemRequest, BatchOperation, 
    BatchResponse, BatchItemResponse, Fault, FaultError
)


class MockObject:
    qbo_object_name = "MockObject"
    
    def __init__(self, name):
        self.name = name
    
    def to_json(self):
        return json.dumps({"name": self.name})
    
    @classmethod
    def from_json(cls, data):
        return cls(data.get("name", ""))


@given(st.text(min_size=1).filter(lambda x: x not in ["create", "update", "delete"]))
def test_batch_manager_invalid_operations_error_format(operation):
    try:
        BatchManager(operation)
        assert False, f"Should have raised exception for invalid operation: {operation}"
    except QuickbooksException as e:
        expected = "Operation not supported."
        actual = e.message
        assert actual == expected, f"Expected message '{expected}' but got '{actual}'"


@given(
    st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=2, max_size=10),
    st.floats(min_value=0.1, max_value=0.9)
)
def test_batch_results_partial_response(obj_list, missing_ratio):
    manager = BatchManager("create")
    batch = manager.list_to_batch_request(obj_list)
    
    num_to_skip = max(1, int(len(obj_list) * missing_ratio))
    
    json_data = {
        'BatchItemResponse': []
    }
    
    for i, item in enumerate(batch.BatchItemRequest):
        if i >= num_to_skip:
            response_item = {
                'bId': item.bId,
                'MockObject': {'name': item.get_object().name}
            }
            json_data['BatchItemResponse'].append(response_item)
    
    try:
        response = manager.batch_results_to_list(json_data, batch, obj_list)
        
        if len(json_data['BatchItemResponse']) < len(batch.BatchItemRequest):
            assert False, "Should have raised an exception when responses are missing"
    except (IndexError, KeyError):
        pass


@given(st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=2, max_size=10))
def test_batch_results_duplicate_bid(obj_list):
    manager = BatchManager("create")
    batch = manager.list_to_batch_request(obj_list)
    
    duplicate_bid = batch.BatchItemRequest[0].bId
    
    json_data = {
        'BatchItemResponse': []
    }
    
    for item in batch.BatchItemRequest:
        response_item = {
            'bId': duplicate_bid,
            'MockObject': {'name': item.get_object().name}
        }
        json_data['BatchItemResponse'].append(response_item)
    
    response = manager.batch_results_to_list(json_data, batch, obj_list)
    
    assert len(response.batch_responses) == len(obj_list)
    for resp in response.batch_responses:
        assert resp.get_object() == batch.BatchItemRequest[0].get_object()


@given(
    st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=1, max_size=100),
    st.integers(min_value=1, max_value=30)
)
def test_save_cumulative_response_aggregation(obj_list, max_items):
    manager = BatchManager("create", max_request_items=max_items)
    
    def mock_process_batch(batch_list, qb=None):
        response = BatchResponse()
        response.original_list = batch_list
        response.batch_responses = [BatchItemResponse() for _ in batch_list]
        response.successes = batch_list[::2]
        response.faults = [Fault() for _ in batch_list[1::2]]
        return response
    
    with patch.object(manager, 'process_batch', side_effect=mock_process_batch):
        result = manager.save(obj_list.copy())
        
        expected_batches = (len(obj_list) + max_items - 1) // max_items
        total_items = len(obj_list)
        
        assert len(result.original_list) == total_items
        assert len(result.batch_responses) == total_items
        assert len(result.successes) == (total_items + 1) // 2
        assert len(result.faults) == total_items // 2


@given(st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=1, max_size=10))
def test_batch_results_wrong_object_type_in_response(obj_list):
    manager = BatchManager("create")
    batch = manager.list_to_batch_request(obj_list)
    
    json_data = {
        'BatchItemResponse': []
    }
    
    for item in batch.BatchItemRequest:
        response_item = {
            'bId': item.bId,
            'WrongObjectType': {'name': item.get_object().name}
        }
        json_data['BatchItemResponse'].append(response_item)
    
    try:
        response = manager.batch_results_to_list(json_data, batch, obj_list)
        assert len(response.faults) == 0
        assert len(response.successes) == 0
    except KeyError:
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])