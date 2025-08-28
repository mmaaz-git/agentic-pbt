import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.batch import BatchManager
from quickbooks.objects.batchrequest import BatchItemResponse


class TestObject:
    qbo_object_name = "TestObject"
    
    def __init__(self, name):
        self.name = name
    
    def to_json(self):
        return json.dumps({"name": self.name})
    
    @classmethod
    def from_json(cls, data):
        return cls(data.get("name", ""))


def test_missing_batch_response():
    manager = BatchManager("create")
    
    obj1 = TestObject("object1")
    obj2 = TestObject("object2")
    obj3 = TestObject("object3")
    obj_list = [obj1, obj2, obj3]
    
    batch = manager.list_to_batch_request(obj_list)
    
    print(f"Created batch with {len(batch.BatchItemRequest)} items")
    print(f"bIds: {[item.bId for item in batch.BatchItemRequest]}")
    
    json_data = {
        'BatchItemResponse': [
            {
                'bId': batch.BatchItemRequest[0].bId,
                'TestObject': {'name': 'object1'}
            },
            {
                'bId': batch.BatchItemRequest[2].bId,
                'TestObject': {'name': 'object3'}
            }
        ]
    }
    
    print(f"\nProviding only {len(json_data['BatchItemResponse'])} responses for {len(batch.BatchItemRequest)} requests")
    
    try:
        response = manager.batch_results_to_list(json_data, batch, obj_list)
        print(f"\nNo exception raised!")
        print(f"Response has {len(response.batch_responses)} batch_responses")
        print(f"Response has {len(response.successes)} successes")
        print(f"Response has {len(response.faults)} faults")
        
        return True
        
    except IndexError as e:
        print(f"\nIndexError raised (expected): {e}")
        return False


if __name__ == "__main__":
    bug_found = test_missing_batch_response()
    if bug_found:
        print("\n✗ BUG CONFIRMED: batch_results_to_list doesn't validate that all batch items have responses!")
    else:
        print("\n✓ No bug: IndexError was properly raised for missing responses")