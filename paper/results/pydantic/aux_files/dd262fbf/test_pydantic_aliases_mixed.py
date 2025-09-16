import pydantic.aliases
from hypothesis import given, strategies as st, assume, settings


@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3),
    st.lists(st.integers(min_value=0, max_value=3), min_size=0, max_size=3),
    st.one_of(st.text(), st.integers(), st.none())
)
def test_alias_path_mixed_search(string_keys, int_indices, value):
    """Test search with mixed string keys and integer indices"""
    # Build a path mixing strings and integers
    path_elements = []
    
    # Interleave strings and integers
    for i, key in enumerate(string_keys):
        path_elements.append(key)
        if i < len(int_indices):
            path_elements.append(int_indices[i])
    
    assume(len(path_elements) > 0)
    assume(not isinstance(path_elements[-1], int))  # Last element should be string
    
    path = pydantic.aliases.AliasPath(path_elements[0], *path_elements[1:])
    
    # Build the corresponding nested structure
    def build_structure(elements, val):
        if not elements:
            return val
        
        first = elements[0]
        rest = elements[1:]
        
        if len(rest) == 0:
            # Last element
            return {first: val}
        
        next_elem = rest[0]
        if isinstance(next_elem, int):
            # Next is integer, create list
            list_size = next_elem + 1
            result_list = [None] * list_size
            result_list[next_elem] = build_structure(rest[1:], val)
            return {first: result_list}
        else:
            # Next is string, create dict
            return {first: build_structure(rest, val)}
    
    data = build_structure(path_elements, value)
    result = path.search_dict_for_path(data)
    assert result == value


@given(
    st.text(min_size=1),
    st.integers(min_value=0, max_value=5),
    st.text(min_size=1),
    st.one_of(st.text(), st.integers(), st.none())
)
def test_alias_path_list_access(key1, index, key2, value):
    """Test that list access works correctly in paths"""
    path = pydantic.aliases.AliasPath(key1, index, key2)
    
    # Create structure with list
    data = {
        key1: [
            {key2: f'wrong_{i}'} if i != index else {key2: value}
            for i in range(index + 1)
        ]
    }
    
    result = path.search_dict_for_path(data)
    assert result == value


@given(
    st.text(min_size=1),
    st.integers(min_value=-5, max_value=-1),
    st.text(min_size=1),
    st.one_of(st.text(), st.integers())
)  
def test_alias_path_negative_index(key1, neg_index, key2, value):
    """Test negative indices in paths"""
    path = pydantic.aliases.AliasPath(key1, neg_index, key2)
    
    # Create list with enough elements
    list_size = abs(neg_index) + 2
    data = {
        key1: [
            {key2: f'value_{i}'} for i in range(list_size)
        ]
    }
    # Set the value at the negative index position
    data[key1][neg_index] = {key2: value}
    
    result = path.search_dict_for_path(data)
    assert result == value