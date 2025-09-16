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


@given(st.sampled_from(["create", "update", "delete"]))
def test_batch_manager_valid_operations(operation):
    manager = BatchManager(operation)
    assert manager._operation == operation


@given(st.text(min_size=1).filter(lambda x: x not in ["create", "update", "delete"]))
def test_batch_manager_invalid_operations(operation):
    try:
        BatchManager(operation)
        assert False, f"Should have raised exception for invalid operation: {operation}"
    except QuickbooksException as e:
        assert str(e) == "Operation not supported."


@given(st.integers(min_value=1, max_value=100))
def test_batch_manager_max_items_property(max_items):
    manager = BatchManager("create", max_request_items=max_items)
    assert manager._max_request_items == max_items


class MockObject:
    def __init__(self, name):
        self.name = name
        self.qbo_object_name = "MockObject"
    
    def to_json(self):
        return json.dumps({"name": self.name})
    
    @classmethod
    def from_json(cls, data):
        return cls(data.get("name", ""))


@given(
    st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=1, max_size=100),
    st.integers(min_value=1, max_value=30)
)
def test_save_preserves_list_length(obj_list, max_items):
    manager = BatchManager("create", max_request_items=max_items)
    original_count = len(obj_list)
    
    with patch.object(manager, 'process_batch') as mock_process:
        response = BatchResponse()
        response.original_list = obj_list[:max_items] if len(obj_list) > max_items else obj_list
        response.batch_responses = []
        response.successes = []
        response.faults = []
        mock_process.return_value = response
        
        result = manager.save(obj_list.copy())
        
        total_processed = sum(len(call[0][0]) for call in mock_process.call_args_list)
        assert total_processed == original_count


@given(
    st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=1, max_size=100),
    st.integers(min_value=1, max_value=30)
)
def test_save_respects_max_batch_size(obj_list, max_items):
    manager = BatchManager("create", max_request_items=max_items)
    
    with patch.object(manager, 'process_batch') as mock_process:
        response = BatchResponse()
        response.original_list = []
        response.batch_responses = []
        response.successes = []
        response.faults = []
        mock_process.return_value = response
        
        manager.save(obj_list.copy())
        
        for call in mock_process.call_args_list:
            batch_size = len(call[0][0])
            assert batch_size <= max_items, f"Batch size {batch_size} exceeds max {max_items}"


@given(st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=1, max_size=50))
def test_list_to_batch_request_uuid_uniqueness(obj_list):
    manager = BatchManager("create")
    batch = manager.list_to_batch_request(obj_list)
    
    uuids = [item.bId for item in batch.BatchItemRequest]
    assert len(uuids) == len(set(uuids)), "Duplicate UUIDs found in batch items"
    assert len(uuids) == len(obj_list), "Number of batch items doesn't match input list"


@given(st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=1, max_size=50))
def test_list_to_batch_request_operation_consistency(obj_list):
    for operation in ["create", "update", "delete"]:
        manager = BatchManager(operation)
        batch = manager.list_to_batch_request(obj_list)
        
        for item in batch.BatchItemRequest:
            assert item.operation == operation
            assert item.get_object() in obj_list


@given(st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=1, max_size=20))
def test_batch_results_to_list_preserves_objects(obj_list):
    manager = BatchManager("create")
    batch = manager.list_to_batch_request(obj_list)
    
    json_data = {
        'BatchItemResponse': []
    }
    
    for item in batch.BatchItemRequest:
        response_item = {
            'bId': item.bId,
            'MockObject': {'name': item.get_object().name}
        }
        json_data['BatchItemResponse'].append(response_item)
    
    response = manager.batch_results_to_list(json_data, batch, obj_list)
    
    assert len(response.batch_responses) == len(obj_list)
    assert len(response.successes) == len(obj_list)
    assert len(response.faults) == 0
    assert response.original_list == obj_list


@given(
    st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=1, max_size=20),
    st.floats(min_value=0, max_value=1)
)
def test_batch_results_fault_success_partition(obj_list, fault_ratio):
    manager = BatchManager("create")
    batch = manager.list_to_batch_request(obj_list)
    
    json_data = {
        'BatchItemResponse': []
    }
    
    num_faults = int(len(obj_list) * fault_ratio)
    
    for i, item in enumerate(batch.BatchItemRequest):
        if i < num_faults:
            response_item = {
                'bId': item.bId,
                'Fault': {
                    'type': 'ValidationFault',
                    'Error': [{
                        'Message': 'Test error',
                        'code': '2000',
                        'Detail': 'Test detail'
                    }]
                }
            }
        else:
            response_item = {
                'bId': item.bId,
                'MockObject': {'name': item.get_object().name}
            }
        json_data['BatchItemResponse'].append(response_item)
    
    response = manager.batch_results_to_list(json_data, batch, obj_list)
    
    assert len(response.batch_responses) == len(obj_list)
    assert len(response.successes) + len(response.faults) == len(obj_list)
    assert len(response.faults) == num_faults
    assert len(response.successes) == len(obj_list) - num_faults


@given(st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=1, max_size=10))
def test_batch_results_missing_response_item(obj_list):
    manager = BatchManager("create")
    batch = manager.list_to_batch_request(obj_list)
    
    json_data = {
        'BatchItemResponse': []
    }
    
    for i, item in enumerate(batch.BatchItemRequest):
        if i < len(batch.BatchItemRequest) - 1:
            response_item = {
                'bId': item.bId,
                'MockObject': {'name': item.get_object().name}
            }
            json_data['BatchItemResponse'].append(response_item)
    
    try:
        response = manager.batch_results_to_list(json_data, batch, obj_list)
        assert False, "Should have raised an exception for missing response"
    except IndexError:
        pass


@given(st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=1, max_size=10))
def test_batch_results_mismatched_bid(obj_list):
    manager = BatchManager("create")
    batch = manager.list_to_batch_request(obj_list)
    
    json_data = {
        'BatchItemResponse': []
    }
    
    for item in batch.BatchItemRequest:
        response_item = {
            'bId': str(uuid.uuid4()),  # Wrong bId
            'MockObject': {'name': item.get_object().name}
        }
        json_data['BatchItemResponse'].append(response_item)
    
    try:
        response = manager.batch_results_to_list(json_data, batch, obj_list)
        assert False, "Should have raised an exception for mismatched bId"
    except IndexError:
        pass


@given(st.lists(st.builds(MockObject, st.text(min_size=1)), min_size=1, max_size=50))
def test_convenience_functions_operation_setting(obj_list):
    with patch('quickbooks.batch.BatchManager.save') as mock_save:
        mock_save.return_value = BatchResponse()
        
        batch_create(obj_list)
        assert mock_save.called
        
        batch_update(obj_list)
        assert mock_save.call_count == 2
        
        batch_delete(obj_list)
        assert mock_save.call_count == 3


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])