import sys
import json
import uuid
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.batch import BatchManager


class TestObject:
    qbo_object_name = "TestObject"
    
    def __init__(self, name):
        self.name = name
    
    def to_json(self):
        return json.dumps({"name": self.name})
    
    @classmethod
    def from_json(cls, data):
        return cls(data.get("name", ""))


def test_invalid_bid_response():
    manager = BatchManager("create")
    
    obj1 = TestObject("object1")
    obj2 = TestObject("object2")
    obj_list = [obj1, obj2]
    
    batch = manager.list_to_batch_request(obj_list)
    
    print(f"Created batch with {len(batch.BatchItemRequest)} items")
    print(f"Original bIds: {[item.bId for item in batch.BatchItemRequest]}")
    
    fake_bid = str(uuid.uuid4())
    json_data = {
        'BatchItemResponse': [
            {
                'bId': batch.BatchItemRequest[0].bId,
                'TestObject': {'name': 'object1'}
            },
            {
                'bId': fake_bid,
                'TestObject': {'name': 'object2'}
            }
        ]
    }
    
    print(f"\nSecond response has fake bId: {fake_bid}")
    
    try:
        response = manager.batch_results_to_list(json_data, batch, obj_list)
        print(f"\nNo exception raised!")
        print(f"Response has {len(response.batch_responses)} batch_responses")
        print(f"Response has {len(response.successes)} successes")
        
        return False
        
    except IndexError as e:
        print(f"\nIndexError raised (expected): {e}")
        print("This occurs because the list comprehension finds no matching bId")
        return True


if __name__ == "__main__":
    exception_raised = test_invalid_bid_response()
    if exception_raised:
        print("\n✓ IndexError properly raised for invalid bId")
    else:
        print("\n✗ BUG: Invalid bId was accepted without error!")