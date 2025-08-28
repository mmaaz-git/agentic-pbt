"""Demonstrate real-world impact of the mutation bug in _get_questions."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.resolver import _get_questions, prompt
from InquirerPy.exceptions import RequiredKeyNotFound

def demonstrate_problem_scenario():
    """Show how the mutation bug could cause problems in real usage."""
    
    print("Scenario: Using the same question list for multiple prompts")
    print("="*60)
    
    # User creates a base set of questions
    base_questions = [
        {"type": "input", "message": "What's your name?", "name": "name"},
        {"type": "input", "message": "What's your email?", "name": "email"},
    ]
    
    print(f"Original questions: {len(base_questions)} questions")
    
    # Scenario 1: Internal code might modify the questions list
    # This simulates what could happen inside prompt() or other internal functions
    processed = _get_questions(base_questions)
    
    # Some internal processing might add temporary fields
    for q in processed:
        q["_internal_flag"] = True  # Simulating internal modification
    
    print(f"\nAfter internal processing:")
    print(f"Original questions now have internal flags: {base_questions[0].get('_internal_flag')}")
    
    # Scenario 2: Multiple calls accumulate modifications
    print("\n" + "-"*40)
    print("Multiple processing calls:")
    
    questions_for_user1 = [
        {"type": "input", "message": "User 1 question", "name": "user1"},
    ]
    
    # First call
    result1 = _get_questions(questions_for_user1)
    result1.append({"type": "input", "message": "Dynamic question 1", "name": "dyn1"})
    
    # Second call with the "same" original questions
    result2 = _get_questions(questions_for_user1)
    result2.append({"type": "input", "message": "Dynamic question 2", "name": "dyn2"})
    
    print(f"Original list after two calls: {len(questions_for_user1)} questions")
    print(f"Expected: 1, Actual: {len(questions_for_user1)}")
    print(f"Questions: {[q['name'] for q in questions_for_user1]}")
    
    return len(questions_for_user1) > 1  # Returns True if bug manifested

def test_with_hypothesis():
    """Property-based test showing the mutation issue."""
    from hypothesis import given, strategies as st
    
    @given(st.lists(st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.text(min_size=1, max_size=10),
        min_size=1, max_size=3
    ), min_size=1, max_size=5))
    def test_get_questions_no_mutation(questions):
        """_get_questions should not allow mutations to affect the original."""
        # Add required fields
        for q in questions:
            q["type"] = "input"
            q["message"] = "test"
        
        original_length = len(questions)
        original_copy = questions.copy()
        
        result = _get_questions(questions)
        
        # Modify the result
        if result:
            result.append({"extra": "question"})
            result[0]["modified"] = True
        
        # Check if original was affected
        assert len(questions) == original_length, f"Original list was mutated! Length changed from {original_length} to {len(questions)}"
        
        # This will fail because _get_questions returns the same object
        assert questions == original_copy, "Original list contents were modified!"
    
    try:
        test_get_questions_no_mutation()
        print("\nHypothesis test passed (no mutation detected)")
        return False
    except AssertionError as e:
        print(f"\nHypothesis test FAILED: {e}")
        print("This confirms the mutation bug!")
        return True

if __name__ == "__main__":
    bug1 = demonstrate_problem_scenario()
    bug2 = test_with_hypothesis()
    
    if bug1 or bug2:
        print("\n" + "="*60)
        print("CONFIRMED BUG:")
        print("The _get_questions function returns the same list object")
        print("instead of a copy, allowing unintended mutations that can")
        print("affect the original questions list and cause unexpected behavior.")
        print("="*60)