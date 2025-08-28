"""Test for potential mutation bug in _get_questions."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.resolver import _get_questions

def test_mutation_issue():
    """Test if _get_questions returns the same list object, allowing mutations."""
    
    # Create an original list of questions
    original_questions = [
        {"type": "input", "message": "Question 1", "name": "q1"},
        {"type": "input", "message": "Question 2", "name": "q2"},
    ]
    
    # Get the result from _get_questions
    result = _get_questions(original_questions)
    
    print(f"Original list id: {id(original_questions)}")
    print(f"Result list id: {id(result)}")
    print(f"Are they the same object? {result is original_questions}")
    
    # If they're the same object, modifying result will modify original
    if result is original_questions:
        print("\nWARNING: _get_questions returns the same list object!")
        print("This means modifications to the result will affect the original list.")
        
        # Demonstrate the issue
        result.append({"type": "input", "message": "Added question", "name": "q3"})
        print(f"\nAfter appending to result:")
        print(f"Original list length: {len(original_questions)}")
        print(f"Result list length: {len(result)}")
        print(f"Original list: {original_questions}")
        
        # This could be problematic if the function is called multiple times
        # or if the caller expects the original list to remain unchanged
        return True  # Bug found
    else:
        print("\n_get_questions returns a copy of the list (safe from mutations)")
        return False  # No bug

def test_dict_to_list_mutation():
    """Test if dict input creates a new list (should be safe)."""
    
    original_question = {"type": "input", "message": "Question", "name": "q"}
    result = _get_questions(original_question)
    
    print(f"\nDict input test:")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
    # Modify the result
    result.append({"type": "input", "message": "Added", "name": "added"})
    
    # Original dict should not be affected (can't append to dict)
    print(f"Original dict unchanged: {original_question}")
    
def test_empty_list_mutation():
    """Test empty list case specifically."""
    
    original = []
    result = _get_questions(original)
    
    print(f"\nEmpty list test:")
    print(f"Are they the same object? {result is original}")
    
    if result is original:
        result.append({"type": "input", "message": "Added to empty", "name": "q"})
        print(f"After modification - Original list: {original}")
        print("BUG: Empty list is returned as-is, allowing external mutation!")
        return True
    return False

if __name__ == "__main__":
    bug1 = test_mutation_issue()
    test_dict_to_list_mutation()
    bug2 = test_empty_list_mutation()
    
    if bug1 or bug2:
        print("\n" + "="*60)
        print("POTENTIAL BUG FOUND:")
        print("_get_questions returns the same list object when given a list,")
        print("which allows unintended mutations of the original list.")
        print("="*60)