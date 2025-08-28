"""Confirm the exact bug in troposphere.utils.get_events"""

import troposphere.utils as utils


def test_sum_behavior_with_iterables():
    """Test how sum() behaves with different types of iterables"""
    
    print("Testing sum() behavior with different types:\n")
    
    # Case 1: Normal lists (what the code expects)
    list_of_lists = [[1, 2], [3, 4]]
    print(f"sum([[1, 2], [3, 4]], []) = {sum(list_of_lists, [])}")
    print("✓ Works correctly with lists\n")
    
    # Case 2: What actually happens - non-list iterables
    class IterableResponse:
        """Simulates AWS SDK response object"""
        def __init__(self, data):
            self.data = data
            self.next_token = None
            
        def __iter__(self):
            return iter(self.data)
    
    # This is what get_events does:
    event_list = []
    response1 = IterableResponse([1, 2])
    response2 = IterableResponse([3, 4])
    event_list.append(response1)  # BUG: appending object, not list
    event_list.append(response2)
    
    print("When appending response objects directly:")
    print(f"event_list = {event_list}")
    
    try:
        result = sum(event_list, [])
        print(f"sum(event_list, []) = {result}")
        print(f"Type of result: {type(result)}")
        print("✗ This doesn't work as expected!\n")
    except TypeError as e:
        print(f"✗ TypeError: {e}\n")
    
    # Case 3: What the code SHOULD do
    event_list_correct = []
    event_list_correct.append(list(response1))  # Convert to list first
    event_list_correct.append(list(response2))
    
    print("Correct approach - converting to list first:")
    print(f"event_list_correct = {event_list_correct}")
    result = sum(event_list_correct, [])
    print(f"sum(event_list_correct, []) = {result}")
    print("✓ This works correctly!\n")
    
    # The actual bug manifestation
    print("THE BUG:")
    print("-------")
    print("Line 14 in utils.py does: event_list.append(events)")
    print("It should do: event_list.append(list(events))")
    print("\nWithout converting to list, sum() doesn't concatenate the items properly,")
    print("leading to incorrect behavior and empty results.")


if __name__ == "__main__":
    test_sum_behavior_with_iterables()