"""Property-based tests for InquirerPy.resolver module."""

import sys
import copy
from typing import Any, Dict, List
from hypothesis import given, strategies as st, assume, settings
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.resolver import _get_questions, _get_question, prompt
from InquirerPy.exceptions import InvalidArgument, RequiredKeyNotFound

# Strategy for valid question types
valid_question_types = st.sampled_from([
    "confirm", "filepath", "password", "input", 
    "list", "checkbox", "rawlist", "expand", "fuzzy", "number"
])

# Strategy for basic question dictionary
def question_dict(with_required=True):
    """Generate a valid question dictionary."""
    base = {
        "message": st.text(min_size=1, max_size=100),
        "default": st.one_of(st.text(), st.integers(), st.booleans(), st.none()),
    }
    if with_required:
        base["type"] = valid_question_types
        base["name"] = st.text(min_size=1, max_size=50)
    
    return st.fixed_dictionaries(base, optional={
        "when": st.just(lambda x: True),
        "keybindings": st.dictionaries(st.text(min_size=1), st.lists(st.dictionaries(st.text(), st.text()))),
    })


# Test 1: _get_questions should always return a list
@given(st.one_of(
    question_dict(with_required=True),
    st.lists(question_dict(with_required=True), min_size=0, max_size=10)
))
def test_get_questions_always_returns_list(questions):
    """_get_questions should always return a list, regardless of input type."""
    result = _get_questions(questions)
    assert isinstance(result, list)
    
    # If input was a dict, output should be a list with one element
    if isinstance(questions, dict):
        assert len(result) == 1
        assert result[0] == questions
    else:
        assert result == questions


# Test 2: _get_questions should raise InvalidArgument for invalid types
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.text(),
    st.tuples(st.integers()),
    st.sets(st.integers())
))
def test_get_questions_invalid_type_raises(questions):
    """_get_questions should raise InvalidArgument for non-list/dict inputs."""
    try:
        _get_questions(questions)
        assert False, "Should have raised InvalidArgument"
    except InvalidArgument as e:
        assert "argument questions should be type of list or dictionary" in str(e)


# Test 3: _get_question should not mutate the original dictionary
@given(
    question_dict(with_required=True),
    st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.integers(), st.booleans()), min_size=0, max_size=5),
    st.integers(min_value=0, max_value=100)
)
def test_get_question_no_mutation(question, result, index):
    """_get_question should not mutate the original question dictionary."""
    # Ensure question has required keys
    question["type"] = "input"
    question["message"] = "Test message"
    question["name"] = f"question_{index}"
    
    original_question = copy.deepcopy(question)
    returned_question, q_type, q_name, q_message = _get_question(question, result, index)
    
    # Original should not be modified
    assert question == original_question
    
    # Returned question should not have type, name, message keys
    if returned_question is not None:
        assert "type" not in returned_question
        assert "name" not in returned_question
        assert "message" not in returned_question


# Test 4: _get_question should properly extract required fields
@given(
    valid_question_types,
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=50),
    st.integers(min_value=0, max_value=100)
)
def test_get_question_extracts_fields(q_type, message, name, index):
    """_get_question should properly extract type, name, and message fields."""
    question = {
        "type": q_type,
        "message": message,
        "name": name,
    }
    
    result = {}
    returned_question, returned_type, returned_name, returned_message = _get_question(
        question.copy(), result, index
    )
    
    assert returned_type == q_type
    assert returned_name == name
    assert returned_message == message
    assert returned_question == {}  # All required keys should be popped


# Test 5: _get_question should use index as name if name is missing
@given(
    valid_question_types,
    st.text(min_size=1, max_size=100),
    st.integers(min_value=0, max_value=1000)
)
def test_get_question_uses_index_when_no_name(q_type, message, index):
    """_get_question should use index as name when name key is missing."""
    question = {
        "type": q_type,
        "message": message,
    }
    
    result = {}
    _, _, returned_name, _ = _get_question(question.copy(), result, index)
    
    assert returned_name == index


# Test 6: _get_question handles 'when' condition properly
@given(
    question_dict(with_required=True),
    st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.integers()), min_size=0, max_size=5),
    st.integers(min_value=0, max_value=100),
    st.booleans()
)
def test_get_question_when_condition(base_question, result, index, should_show):
    """_get_question should handle 'when' condition correctly."""
    # Ensure required fields
    base_question["type"] = "input"
    base_question["message"] = "Test"
    base_question["name"] = f"q_{index}"
    base_question["when"] = lambda r: should_show
    
    returned_question, _, q_name, _ = _get_question(base_question.copy(), result, index)
    
    if should_show:
        assert returned_question is not None
        assert q_name not in result  # Question name shouldn't be in result yet
    else:
        assert returned_question is None
        assert result[q_name] is None  # Question should be marked as None in result


# Test 7: Round-trip property for single dict to list conversion
@given(question_dict(with_required=True))
def test_get_questions_dict_to_list_roundtrip(question):
    """Converting a dict to list via _get_questions preserves the content."""
    question["type"] = "input"
    question["message"] = "Test"
    
    result = _get_questions(question)
    assert len(result) == 1
    assert result[0] == question
    
    # Should be idempotent for lists
    result2 = _get_questions(result)
    assert result2 == result


# Test 8: prompt function should raise RequiredKeyNotFound for missing required keys
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.text(), st.integers(), st.booleans()),
    min_size=0, max_size=5
))
def test_prompt_missing_required_keys(question):
    """prompt should raise RequiredKeyNotFound when type key is missing."""
    # Ensure message exists but type doesn't
    question["message"] = "Test message"
    if "type" in question:
        del question["type"]
    
    try:
        prompt([question])
        assert False, "Should have raised RequiredKeyNotFound"
    except RequiredKeyNotFound:
        pass  # Expected
    except KeyError:
        # KeyError is also acceptable since the code catches it and raises RequiredKeyNotFound
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])