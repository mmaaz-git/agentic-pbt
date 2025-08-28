import ast
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import isort.literal
from isort.literal import assignment, assignments
from isort.settings import Config

# Test 1: assignments() preserves all variable assignments
@given(st.dictionaries(
    st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True),
    st.text(min_size=1).filter(lambda x: '\n' not in x),
    min_size=1
))
def test_assignments_preserves_all(var_dict):
    # Create assignment code
    lines = []
    for var, val in var_dict.items():
        lines.append(f"{var} = {val}")
    code = "\n".join(lines) + "\n"
    
    # Sort assignments
    result = assignments(code)
    
    # Parse result back
    result_lines = result.strip().split("\n")
    result_dict = {}
    for line in result_lines:
        if " = " in line:
            var, val = line.split(" = ", 1)
            result_dict[var] = val
    
    # All original assignments should be preserved
    assert set(var_dict.keys()) == set(result_dict.keys())
    for var in var_dict:
        assert result_dict[var] == var_dict[var]


# Test 2: unique-list removes duplicates
@given(st.lists(st.integers()))
def test_unique_list_removes_duplicates(lst):
    assume(len(lst) > 0)
    code = f"x = {repr(lst)}"
    config = Config()
    
    result = assignment(code, "unique-list", ".py", config)
    
    # Extract the list from result
    _, literal_part = result.split(" = ", 1)
    result_list = ast.literal_eval(literal_part.strip())
    
    # Should have no duplicates
    assert len(result_list) == len(set(result_list))
    # Should contain same unique elements
    assert set(result_list) == set(lst)


# Test 3: list sorting produces sorted output
@given(st.lists(st.integers()))
def test_list_is_sorted(lst):
    code = f"x = {repr(lst)}"
    config = Config()
    
    result = assignment(code, "list", ".py", config)
    
    # Extract the list from result
    _, literal_part = result.split(" = ", 1)
    result_list = ast.literal_eval(literal_part.strip())
    
    # Should be sorted
    assert result_list == sorted(result_list)
    # Should preserve all elements
    assert sorted(result_list) == sorted(lst)


# Test 4: dict sorting preserves all key-value pairs
@given(st.dictionaries(
    st.integers(),
    st.integers(),
    min_size=1
))
def test_dict_preserves_all_pairs(d):
    code = f"x = {repr(d)}"
    config = Config()
    
    result = assignment(code, "dict", ".py", config)
    
    # Extract the dict from result
    _, literal_part = result.split(" = ", 1)
    result_dict = ast.literal_eval(literal_part.strip())
    
    # Should preserve all key-value pairs
    assert result_dict == d
    assert set(result_dict.keys()) == set(d.keys())
    for key in d:
        assert result_dict[key] == d[key]


# Test 5: set sorting produces valid set
@given(st.sets(st.integers()))
def test_set_is_valid(s):
    code = f"x = {repr(s)}"
    config = Config()
    
    result = assignment(code, "set", ".py", config)
    
    # Extract the set from result
    _, literal_part = result.split(" = ", 1)
    result_set = ast.literal_eval(literal_part.strip())
    
    # Should be a set with same elements
    assert isinstance(result_set, set)
    assert result_set == s


# Test 6: tuple sorting produces sorted tuple
@given(st.lists(st.integers()).map(tuple))
def test_tuple_is_sorted(t):
    code = f"x = {repr(t)}"
    config = Config()
    
    result = assignment(code, "tuple", ".py", config)
    
    # Extract the tuple from result
    _, literal_part = result.split(" = ", 1)
    result_tuple = ast.literal_eval(literal_part.strip())
    
    # Should be sorted
    assert result_tuple == tuple(sorted(result_tuple))
    # Should preserve all elements
    assert sorted(result_tuple) == sorted(t)


# Test 7: unique-tuple removes duplicates
@given(st.lists(st.integers()).map(tuple))
def test_unique_tuple_removes_duplicates(t):
    assume(len(t) > 0)
    code = f"x = {repr(t)}"
    config = Config()
    
    result = assignment(code, "unique-tuple", ".py", config)
    
    # Extract the tuple from result
    _, literal_part = result.split(" = ", 1)
    result_tuple = ast.literal_eval(literal_part.strip())
    
    # Should have no duplicates
    assert len(result_tuple) == len(set(result_tuple))
    # Should contain same unique elements
    assert set(result_tuple) == set(t)


# Test 8: Round-trip property for assignments with varying whitespace
@given(st.dictionaries(
    st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True),
    st.text(min_size=1).filter(lambda x: '\n' not in x),
    min_size=1
))
def test_assignments_idempotent(var_dict):
    # Create assignment code
    lines = []
    for var, val in var_dict.items():
        lines.append(f"{var} = {val}")
    code = "\n".join(lines) + "\n"
    
    # Sort once
    result1 = assignments(code)
    # Sort twice
    result2 = assignments(result1)
    
    # Should be idempotent
    assert result1 == result2


# Test 9: Metamorphic - sorting dict by values
@given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=2))
def test_dict_sorting_by_values(d):
    code = f"x = {repr(d)}"
    config = Config()
    
    result = assignment(code, "dict", ".py", config)
    
    # Extract the dict from result
    _, literal_part = result.split(" = ", 1)
    # Since dicts maintain insertion order in Python 3.7+, 
    # we can check if items are sorted by value
    result_str = literal_part.strip()
    
    # Parse to get the actual dict
    result_dict = ast.literal_eval(result_str)
    
    # Get items as list to check ordering
    items = list(result_dict.items())
    values = [v for k, v in items]
    
    # Values should be in sorted order
    assert values == sorted(values)