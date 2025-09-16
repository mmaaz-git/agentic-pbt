import pydantic.aliases
from hypothesis import given, strategies as st, assume


@given(
    st.lists(
        st.one_of(st.text(min_size=1), st.integers()),
        min_size=1,
        max_size=10
    )
)
def test_alias_path_convert_to_aliases_identity(path_elements):
    """Property: AliasPath.convert_to_aliases() returns the exact path list"""
    path = pydantic.aliases.AliasPath(path_elements[0], *path_elements[1:])
    converted = path.convert_to_aliases()
    assert path.path == converted


@given(
    st.lists(
        st.text(min_size=1),
        min_size=1,
        max_size=5
    ),
    st.one_of(st.text(), st.integers(), st.none(), st.booleans())
)
def test_alias_path_search_dict_round_trip(path_elements, value):
    """Property: If we build a dict from a path (string keys only), searching should find the value"""
    path = pydantic.aliases.AliasPath(path_elements[0], *path_elements[1:])
    
    # Build nested dict from path (simplified - string keys only)
    data = {}
    current = data
    for element in path_elements[:-1]:
        current[element] = {}
        current = current[element]
    
    # Set the final value
    current[path_elements[-1]] = value
    
    # Search should find the value
    result = path.search_dict_for_path(data)
    assert result == value


@given(
    st.lists(
        st.one_of(
            st.text(min_size=1),
            st.builds(
                pydantic.aliases.AliasPath,
                st.text(min_size=1),
                *[st.one_of(st.text(min_size=1), st.integers()) for _ in range(3)]
            )
        ),
        min_size=1,
        max_size=5
    )
)
def test_alias_choices_convert_preserves_structure(choices_list):
    """Property: AliasChoices.convert_to_aliases preserves order and count"""
    choices = pydantic.aliases.AliasChoices(choices_list[0], *choices_list[1:])
    converted = choices.convert_to_aliases()
    
    # Should have same number of choices
    assert len(choices.choices) == len(converted)
    
    # Each choice should be converted to a list
    for i, choice in enumerate(choices.choices):
        if isinstance(choice, pydantic.aliases.AliasPath):
            assert converted[i] == choice.path
        else:
            assert converted[i] == [choice]


@given(st.text(min_size=1))
def test_alias_generator_deterministic(field_name):
    """Property: AliasGenerator.generate_aliases is deterministic"""
    def transform(s: str) -> str:
        return s.upper()
    
    gen = pydantic.aliases.AliasGenerator(
        alias=transform,
        validation_alias=lambda s: s.lower(),
        serialization_alias=lambda s: s.replace('_', '-')
    )
    
    result1 = gen.generate_aliases(field_name)
    result2 = gen.generate_aliases(field_name)
    
    assert result1 == result2
    assert result1[0] == field_name.upper()
    assert result1[1] == field_name.lower()
    assert result1[2] == field_name.replace('_', '-')


@given(
    st.lists(
        st.one_of(st.text(min_size=1), st.integers()),
        min_size=1,
        max_size=5
    )
)
def test_alias_path_equality(path_elements):
    """Property: AliasPath objects with same elements should be equal"""
    path1 = pydantic.aliases.AliasPath(path_elements[0], *path_elements[1:])
    path2 = pydantic.aliases.AliasPath(path_elements[0], *path_elements[1:])
    
    assert path1 == path2
    assert path1.path == path2.path


@given(
    st.lists(
        st.one_of(st.text(min_size=1), st.integers()),
        min_size=1,
        max_size=5
    )
)
def test_alias_choices_equality(choices_elements):
    """Property: AliasChoices objects with same elements should be equal"""
    choices1 = pydantic.aliases.AliasChoices(choices_elements[0], *choices_elements[1:])
    choices2 = pydantic.aliases.AliasChoices(choices_elements[0], *choices_elements[1:])
    
    assert choices1 == choices2
    assert choices1.choices == choices2.choices


@given(st.text(min_size=1))
def test_alias_generator_with_none_functions(field_name):
    """Property: AliasGenerator with None functions should return None for those"""
    gen = pydantic.aliases.AliasGenerator(
        alias=lambda s: s.upper(),
        validation_alias=None,
        serialization_alias=None
    )
    
    result = gen.generate_aliases(field_name)
    assert result[0] == field_name.upper()
    assert result[1] is None
    assert result[2] is None


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=5),
    st.lists(st.one_of(st.text(), st.integers(), st.none()), min_size=1, max_size=5)
)
def test_alias_path_search_missing_path(path_elements, values):
    """Property: search_dict_for_path returns PydanticUndefined for missing paths"""
    path = pydantic.aliases.AliasPath(path_elements[0], *path_elements[1:])
    
    # Create a dict that doesn't contain this path
    data = {f'different_{i}': v for i, v in enumerate(values)}
    
    result = path.search_dict_for_path(data)
    assert result == pydantic.aliases.PydanticUndefined


@given(
    st.dictionaries(
        st.text(min_size=1),
        st.one_of(
            st.text(),
            st.integers(),
            st.lists(st.one_of(st.text(), st.integers()), max_size=5),
            st.dictionaries(st.text(min_size=1), st.text(), max_size=3)
        ),
        min_size=1,
        max_size=5
    )
)
def test_alias_path_search_single_key(data):
    """Property: Single-element path should find direct keys"""
    assume(len(data) > 0)
    
    # Pick a random key from the dict
    key = list(data.keys())[0]
    expected_value = data[key]
    
    path = pydantic.aliases.AliasPath(key)
    result = path.search_dict_for_path(data)
    
    assert result == expected_value


@given(st.text(min_size=1, max_size=50))
def test_alias_generator_function_application(field_name):
    """Property: Functions are correctly applied to field names"""
    # Create specific transformation functions
    def to_camel(s: str) -> str:
        parts = s.split('_')
        return parts[0] + ''.join(p.capitalize() for p in parts[1:] if p)
    
    def to_snake(s: str) -> str:
        return s.replace('-', '_')
    
    def to_kebab(s: str) -> str:
        return s.replace('_', '-')
    
    gen = pydantic.aliases.AliasGenerator(
        alias=to_camel,
        validation_alias=to_snake,
        serialization_alias=to_kebab
    )
    
    result = gen.generate_aliases(field_name)
    
    # Verify each function was applied
    assert result[0] == to_camel(field_name)
    assert result[1] == to_snake(field_name)
    assert result[2] == to_kebab(field_name)