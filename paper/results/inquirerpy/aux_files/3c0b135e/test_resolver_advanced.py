"""Advanced property-based tests for InquirerPy.resolver module."""

import sys
import copy
from typing import Any, Dict, List
from hypothesis import given, strategies as st, assume, settings, example
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.resolver import _get_questions, _get_question, prompt, question_mapping
from InquirerPy.exceptions import InvalidArgument, RequiredKeyNotFound


# Test for edge cases with empty inputs
@given(st.just([]))
def test_get_questions_empty_list(questions):
    """_get_questions should handle empty list correctly."""
    result = _get_questions(questions)
    assert result == []
    assert result is not questions  # Should return the same object or a copy?


# Test for deeply nested structures
@given(st.lists(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.recursive(
        st.one_of(st.text(), st.integers(), st.booleans()),
        lambda children: st.one_of(
            children,
            st.lists(children, max_size=3),
            st.dictionaries(st.text(min_size=1, max_size=5), children, max_size=3)
        ),
        max_leaves=20
    ),
    min_size=1, max_size=10
), min_size=0, max_size=5))
def test_get_questions_nested_structures(questions):
    """_get_questions should handle nested structures without errors."""
    try:
        result = _get_questions(questions)
        assert isinstance(result, list)
        assert result == questions
    except InvalidArgument:
        # Should only raise for non-list/dict at top level
        assert not isinstance(questions, (list, dict))


# Test _get_question with missing message key
@given(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=50),
    st.integers(min_value=0, max_value=100)
)
def test_get_question_missing_message(q_type, name, index):
    """_get_question should raise KeyError when message is missing."""
    question = {
        "type": q_type,
        "name": name,
        # "message" is missing
    }
    
    result = {}
    try:
        _get_question(question.copy(), result, index)
        assert False, "Should have raised KeyError for missing message"
    except KeyError:
        pass  # Expected


# Test _get_question with missing type key
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=50),
    st.integers(min_value=0, max_value=100)
)
def test_get_question_missing_type(message, name, index):
    """_get_question should raise KeyError when type is missing."""
    question = {
        "message": message,
        "name": name,
        # "type" is missing
    }
    
    result = {}
    try:
        _get_question(question.copy(), result, index)
        assert False, "Should have raised KeyError for missing type"
    except KeyError:
        pass  # Expected


# Test with unicode and special characters
@given(st.dictionaries(
    st.text(alphabet="🔥💀🎉😊🦄", min_size=1, max_size=10),
    st.text(alphabet="🔥💀🎉😊🦄", min_size=1, max_size=10),
    min_size=1, max_size=5
))
def test_get_questions_unicode(questions):
    """_get_questions should handle unicode characters correctly."""
    # Convert to list form
    questions_list = [questions]
    result = _get_questions(questions_list)
    assert result == questions_list


# Test with very large indices
@given(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=100),
    st.integers(min_value=2**31, max_value=2**63-1)  # Large integers
)
def test_get_question_large_index(q_type, message, index):
    """_get_question should handle very large indices correctly."""
    question = {
        "type": q_type,
        "message": message,
        # No name, so index should be used
    }
    
    result = {}
    _, _, returned_name, _ = _get_question(question.copy(), result, index)
    assert returned_name == index


# Test when condition with side effects
@given(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=50),
    st.integers(min_value=0, max_value=100)
)
def test_get_question_when_side_effects(q_type, message, name, index):
    """Test when condition that modifies result dict."""
    call_count = [0]
    
    def when_func(result):
        call_count[0] += 1
        # Try to modify result (side effect)
        result["side_effect"] = "modified"
        return False
    
    question = {
        "type": q_type,
        "message": message,
        "name": name,
        "when": when_func
    }
    
    result = {}
    returned_question, _, _, _ = _get_question(question.copy(), result, index)
    
    assert call_count[0] == 1  # when should be called once
    assert result[name] is None  # Question marked as None
    assert "side_effect" in result  # Side effect should persist
    assert result["side_effect"] == "modified"


# Test _get_question preserves extra keys
@given(
    st.text(min_size=1, max_size=20),
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=50),
    st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda x: x not in ["type", "message", "name", "when"]),
        st.one_of(st.text(), st.integers(), st.booleans()),
        min_size=0, max_size=10
    ),
    st.integers(min_value=0, max_value=100)
)
def test_get_question_preserves_extra_keys(q_type, message, name, extra_keys, index):
    """_get_question should preserve extra keys in the returned question dict."""
    question = {
        "type": q_type,
        "message": message,
        "name": name,
        **extra_keys
    }
    
    result = {}
    returned_question, _, _, _ = _get_question(question.copy(), result, index)
    
    # All extra keys should be preserved
    for key, value in extra_keys.items():
        assert key in returned_question
        assert returned_question[key] == value


# Test invalid question type in prompt
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: x not in question_mapping),
    st.text(min_size=1, max_size=100)
)
def test_prompt_invalid_question_type(invalid_type, message):
    """prompt should raise when question type is not in question_mapping."""
    question = {
        "type": invalid_type,
        "message": message,
        "name": "test"
    }
    
    try:
        prompt([question])
        assert False, f"Should have raised for invalid type: {invalid_type}"
    except (RequiredKeyNotFound, KeyError):
        pass  # Expected


# Test question name collision
@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=5),
    st.text(min_size=1, max_size=50)
)
def test_question_name_collision(messages, shared_name):
    """Test what happens when multiple questions have the same name."""
    questions = []
    for msg in messages:
        questions.append({
            "type": "input",
            "message": msg,
            "name": shared_name,  # All questions have the same name
        })
    
    # This should not raise an error
    result = _get_questions(questions)
    assert len(result) == len(messages)
    
    # Each question in result should still have the same name
    for i, question in enumerate(result):
        assert question["name"] == shared_name


# Test modification during iteration (mutation safety)
@given(st.integers(min_value=1, max_value=10))
def test_get_questions_mutation_during_iteration(n):
    """Test that modifying questions during iteration doesn't cause issues."""
    questions = []
    for i in range(n):
        questions.append({
            "type": "input",
            "message": f"Question {i}",
            "name": f"q{i}",
        })
    
    # Get a reference to the list
    result = _get_questions(questions)
    
    # Try to modify the original list
    questions.append({"type": "input", "message": "New", "name": "new"})
    questions[0]["message"] = "Modified"
    
    # Result should not be affected (if it's a copy)
    # Or it should be affected (if it's the same reference)
    # Either way, it shouldn't crash
    assert len(result) in [n, n+1]  # Could be either depending on implementation


# Test with None values
@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.one_of(st.none(), st.text(), st.integers()),
    min_size=0, max_size=5
))
def test_get_questions_with_none_values(question):
    """Test _get_questions with None values in question dict."""
    question["type"] = "input"
    question["message"] = "Test"
    
    result = _get_questions(question)
    assert len(result) == 1
    assert result[0] == question


# Test extreme nesting in when condition
def test_get_question_recursive_when():
    """Test when condition that references itself indirectly."""
    question = {
        "type": "input",
        "message": "Test",
        "name": "recursive",
        "when": lambda result: "recursive" not in result or result["recursive"] is None
    }
    
    result = {}
    returned_question, _, name, _ = _get_question(question.copy(), result, 0)
    
    # This is an interesting case - the when condition checks if the key exists
    if returned_question is None:
        assert result[name] is None
    else:
        assert name not in result  # Key shouldn't exist yet


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-x"])