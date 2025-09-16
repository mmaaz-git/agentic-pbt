import pydantic.aliases
from hypothesis import given, strategies as st, assume


@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5),
    st.text()
)
def test_alias_path_search_metamorphic(path_keys, extra_key):
    """Metamorphic property: Adding unrelated keys shouldn't affect search result"""
    path = pydantic.aliases.AliasPath(path_keys[0], *path_keys[1:])
    
    # Build nested dict
    def build_dict(keys, value):
        if len(keys) == 1:
            return {keys[0]: value}
        return {keys[0]: build_dict(keys[1:], value)}
    
    value = "test_value"
    data1 = build_dict(path_keys, value)
    result1 = path.search_dict_for_path(data1)
    
    # Add an unrelated key at the top level
    assume(extra_key not in data1)
    data2 = data1.copy()
    data2[extra_key] = "unrelated"
    result2 = path.search_dict_for_path(data2)
    
    # Results should be the same
    assert result1 == result2


@given(
    st.lists(
        st.one_of(st.text(min_size=1), st.integers()),
        min_size=1,
        max_size=10
    )
)
def test_alias_path_double_conversion(elements):
    """Property: Double conversion should be idempotent"""
    path = pydantic.aliases.AliasPath(elements[0], *elements[1:])
    
    converted1 = path.convert_to_aliases()
    # Create new path from converted
    path2 = pydantic.aliases.AliasPath(converted1[0], *converted1[1:])
    converted2 = path2.convert_to_aliases()
    
    assert converted1 == converted2
    assert path.path == path2.path


@given(
    st.lists(st.text(min_size=1), min_size=2, max_size=10)
)
def test_alias_choices_order_independence_for_equality(texts):
    """Test if order matters for equality (it should)"""
    choices1 = pydantic.aliases.AliasChoices(texts[0], *texts[1:])
    
    # Reverse order
    reversed_texts = list(reversed(texts))
    choices2 = pydantic.aliases.AliasChoices(reversed_texts[0], *reversed_texts[1:])
    
    # They should NOT be equal if order is different (unless palindrome)
    if texts != reversed_texts:
        assert choices1 != choices2
    else:
        assert choices1 == choices2


@given(st.text(min_size=1, max_size=50))
def test_alias_generator_function_composition(field):
    """Test composing transformation functions"""
    
    def upper(s: str) -> str:
        return s.upper()
    
    def lower(s: str) -> str:
        return s.lower()
    
    # Generator 1: upper for alias
    gen1 = pydantic.aliases.AliasGenerator(alias=upper)
    result1 = gen1.generate_aliases(field)
    
    # Generator 2: lower for alias  
    gen2 = pydantic.aliases.AliasGenerator(alias=lower)
    result2 = gen2.generate_aliases(field)
    
    # Applying upper then lower should give lowercase
    assert result2[0] == field.lower()
    assert result1[0] == field.upper()
    
    # Composed generator
    def upper_then_lower(s: str) -> str:
        return lower(upper(s))
    
    gen3 = pydantic.aliases.AliasGenerator(alias=upper_then_lower)
    result3 = gen3.generate_aliases(field)
    
    assert result3[0] == field.lower()


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=5),
    st.integers(min_value=0, max_value=10)
)
def test_alias_path_list_bounds_checking(keys, index):
    """Test list bounds checking in search_dict_for_path"""
    # Create path with integer index
    path_elements = keys + [index]
    assume(len(keys) > 0)
    
    path = pydantic.aliases.AliasPath(keys[0], *keys[1:], index)
    
    # Build structure with list of varying sizes
    def build_with_list(keys_list, list_size):
        result = {}
        current = result
        for i, key in enumerate(keys_list[:-1]):
            current[key] = {}
            current = current[key]
        # Last key gets a list
        current[keys_list[-1]] = [f"item_{i}" for i in range(list_size)]
        return result
    
    # Test with list smaller than index
    if index > 0:
        small_data = build_with_list(keys, index - 1)
        result = path.search_dict_for_path(small_data)
        assert result == pydantic.aliases.PydanticUndefined
    
    # Test with list exactly at index
    exact_data = build_with_list(keys, index + 1)
    result = path.search_dict_for_path(exact_data)
    assert result == f"item_{index}"
    
    # Test with list larger than index
    large_data = build_with_list(keys, index + 10)
    result = path.search_dict_for_path(large_data)
    assert result == f"item_{index}"


@given(
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_alias_choices_with_duplicate_choices(choice1, choice2):
    """Test AliasChoices with duplicate values"""
    # Create choices with duplicates
    choices = pydantic.aliases.AliasChoices(choice1, choice2, choice1, choice2)
    
    # Should preserve all including duplicates
    assert len(choices.choices) == 4
    assert choices.choices == [choice1, choice2, choice1, choice2]
    
    # convert_to_aliases should also preserve duplicates
    converted = choices.convert_to_aliases()
    assert len(converted) == 4


@given(st.data())
def test_alias_path_type_mixing_in_path(data):
    """Test paths with mixed types at different positions"""
    
    # Generate a complex mixed path
    path_elements = []
    for _ in range(data.draw(st.integers(min_value=1, max_value=5))):
        element = data.draw(st.one_of(
            st.text(min_size=1, max_size=10),
            st.integers(min_value=-10, max_value=10),
            st.just(""),  # empty string
            st.just(0),   # zero
            st.just(-1),  # negative one
        ))
        path_elements.append(element)
    
    path = pydantic.aliases.AliasPath(path_elements[0], *path_elements[1:])
    
    # Path should preserve exact types and values
    assert path.path == path_elements
    
    # Test convert_to_aliases preserves everything
    assert path.convert_to_aliases() == path_elements
    
    # Test equality with identical path
    path2 = pydantic.aliases.AliasPath(path_elements[0], *path_elements[1:])
    assert path == path2