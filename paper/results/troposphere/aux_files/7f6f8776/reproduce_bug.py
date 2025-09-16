"""Minimal reproduction of the bug in troposphere.utils.get_events"""

from unittest.mock import MagicMock
import troposphere.utils as utils


# Create a mock event
class MockEvent:
    def __init__(self, event_id):
        self.event_id = event_id
        self.resource_status = "CREATE_COMPLETE"
        self.resource_type = "AWS::CloudFormation::Stack"


# Test case: single batch with one event
def test_single_batch():
    print("Testing single batch with one event...")
    
    # Create mock connection
    mock_conn = MagicMock()
    event = MockEvent("event-1")
    
    # Setup mock to return a single batch
    mock_response = MagicMock()
    mock_response.__iter__ = lambda self: iter([event])
    mock_response.next_token = None  # No more pages
    
    mock_conn.describe_stack_events.return_value = mock_response
    
    # Call get_events
    result = list(utils.get_events(mock_conn, "test-stack"))
    
    print(f"Expected: 1 event")
    print(f"Actual: {len(result)} events")
    
    if len(result) == 0:
        print("\nBUG FOUND: get_events returns empty list for single batch!")
        
        # Let's trace through the logic
        print("\nDebugging the issue:")
        print("1. describe_stack_events returns mock_response")
        print("2. mock_response iterates over [event]")
        print("3. event_list.append(events) appends the mock_response")
        print("4. sum(event_list, []) tries to flatten...")
        
        # The issue is that sum() expects lists to concatenate
        # But we're appending the mock response object itself
        event_list = []
        event_list.append(mock_response)
        
        print(f"\nevent_list contains: {event_list}")
        print(f"Type of first element: {type(event_list[0])}")
        
        try:
            flattened = sum(event_list, [])
            print(f"sum(event_list, []) = {flattened}")
        except Exception as e:
            print(f"sum(event_list, []) fails with: {e}")
            
        print("\nThe bug is that get_events appends the response object")
        print("instead of converting it to a list first!")
    else:
        print("Test passed - no bug found")


if __name__ == "__main__":
    test_single_batch()