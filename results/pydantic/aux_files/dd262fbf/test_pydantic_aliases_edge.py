import pydantic.aliases
from hypothesis import given, strategies as st, assume, settings
import sys


@given(st.data())
def test_alias_generator_exception_handling(data):
    """Test AliasGenerator with functions that might raise exceptions"""
    
    # Generate a field name
    field = data.draw(st.text(min_size=1))
    
    # Create functions that might fail on certain inputs
    def may_fail(s: str) -> str:
        if len(s) > 10:
            raise ValueError("Too long")
        return s.upper()
    
    def always_works(s: str) -> str:
        return s.lower()
    
    gen = pydantic.aliases.AliasGenerator(
        alias=may_fail,
        validation_alias=always_works
    )
    
    try:
        result = gen.generate_aliases(field)
        # If it succeeded, the first element should be uppercase
        if len(field) <= 10:
            assert result[0] == field.upper()
            assert result[1] == field.lower()
    except ValueError:
        # Should only happen if field is too long
        assert len(field) > 10


@given(st.text(min_size=0, max_size=1000))
def test_alias_path_empty_string_keys(key):
    """Test AliasPath with empty string keys"""
    
    if key == "":
        # Empty string is valid
        path = pydantic.aliases.AliasPath(key)
        assert path.path == [key]
        
        # Should be able to search for it
        data = {"": "empty_key_value"}
        result = path.search_dict_for_path(data)
        assert result == "empty_key_value"
    else:
        path = pydantic.aliases.AliasPath(key)
        assert path.path == [key]


@given(
    st.lists(
        st.one_of(
            st.text(min_size=0, max_size=100),
            st.integers(min_value=-sys.maxsize, max_value=sys.maxsize)
        ),
        min_size=1,
        max_size=10
    )
)
def test_alias_path_extreme_values(elements):
    """Test AliasPath with extreme integer values and long strings"""
    path = pydantic.aliases.AliasPath(elements[0], *elements[1:])
    
    # Path should store exactly what was given
    assert path.path == elements
    
    # convert_to_aliases should return the same
    assert path.convert_to_aliases() == elements


@given(
    st.recursive(
        st.dictionaries(st.text(min_size=1, max_size=5), st.integers()),
        lambda children: st.dictionaries(
            st.text(min_size=1, max_size=5),
            st.one_of(st.integers(), children)
        ),
        max_leaves=10
    ),
    st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=5)
)
def test_alias_path_deeply_nested(nested_dict, path_keys):
    """Test search_dict_for_path with deeply nested structures"""
    path = pydantic.aliases.AliasPath(path_keys[0], *path_keys[1:])
    
    # This might or might not find something
    result = path.search_dict_for_path(nested_dict)
    
    # Result should either be PydanticUndefined or a value from the dict
    assert result == pydantic.aliases.PydanticUndefined or not isinstance(result, dict)


@given(st.text())
def test_alias_choices_string_normalization(text):
    """Test if AliasChoices does any string normalization"""
    choices = pydantic.aliases.AliasChoices(text)
    
    # Should preserve the exact string
    assert choices.choices == [text]
    
    # convert_to_aliases should wrap it in a list
    assert choices.convert_to_aliases() == [[text]]
    
    # Test with whitespace
    if text != text.strip():
        # Whitespace should be preserved
        assert choices.choices[0] != text.strip()


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=100)
)
def test_alias_choices_many_choices(choice_list):
    """Test AliasChoices with many choices"""
    choices = pydantic.aliases.AliasChoices(choice_list[0], *choice_list[1:])
    
    # All choices should be preserved
    assert len(choices.choices) == len(choice_list)
    assert choices.choices == choice_list
    
    # convert_to_aliases should wrap each in a list
    converted = choices.convert_to_aliases()
    assert len(converted) == len(choice_list)
    for i, choice in enumerate(choice_list):
        assert converted[i] == [choice]


@given(st.text(min_size=1))
def test_alias_generator_identity_functions(field):
    """Test AliasGenerator with identity functions"""
    
    def identity(s: str) -> str:
        return s
    
    gen = pydantic.aliases.AliasGenerator(
        alias=identity,
        validation_alias=identity,
        serialization_alias=identity
    )
    
    result = gen.generate_aliases(field)
    
    # All should be the same
    assert result == (field, field, field)


@given(st.integers(min_value=-1000, max_value=1000))
def test_alias_path_integer_only(index):
    """Test AliasPath when first element is integer"""
    # This should work according to the signature
    path = pydantic.aliases.AliasPath(index)
    assert path.path == [index]
    
    # Searching in a list
    if index >= 0:
        data = list(range(index + 10))
        result = path.search_dict_for_path(data)
        assert result == index
    else:
        # Negative index
        data = list(range(abs(index) + 10))
        result = path.search_dict_for_path(data)
        assert result == data[index]


@given(
    st.one_of(
        st.none(),
        st.integers(),
        st.floats(allow_nan=True, allow_infinity=True),
        st.text()
    )
)
def test_alias_path_search_on_non_dict(value):
    """Test search_dict_for_path when passed non-dict values"""
    path = pydantic.aliases.AliasPath('key')
    
    # Should return PydanticUndefined for non-dict/non-list
    result = path.search_dict_for_path(value)
    
    if isinstance(value, (dict, list)):
        # Might find something
        pass
    else:
        assert result == pydantic.aliases.PydanticUndefined