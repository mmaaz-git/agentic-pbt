import pydantic.aliases
from hypothesis import given, strategies as st, assume, settings
import gc


@given(st.data())
def test_alias_generator_callable_validation(data):
    """Test that AliasGenerator properly validates callable arguments"""
    
    # Try with non-callable values
    non_callable = data.draw(st.one_of(
        st.integers(),
        st.text(),
        st.none(),
        st.lists(st.integers())
    ))
    
    if non_callable is not None and not callable(non_callable):
        try:
            gen = pydantic.aliases.AliasGenerator(alias=non_callable)
            # If this succeeds, it means it accepts non-callables
            # Let's see what happens when we try to use it
            try:
                result = gen.generate_aliases("test")
                # This should fail if non_callable isn't callable
                assert False, f"Expected error with non-callable {non_callable}"
            except TypeError:
                pass  # Expected
        except (TypeError, ValueError):
            pass  # Expected at construction


@given(
    st.lists(st.one_of(st.text(), st.integers()), min_size=1000, max_size=2000)
)
@settings(max_examples=5)
def test_alias_path_large_paths(elements):
    """Test AliasPath with very large paths"""
    path = pydantic.aliases.AliasPath(elements[0], *elements[1:])
    
    # Should handle large paths
    assert len(path.path) == len(elements)
    assert path.path == elements
    
    # Conversion should work
    converted = path.convert_to_aliases()
    assert converted == elements


@given(st.data())
def test_alias_path_search_circular_references(data):
    """Test search_dict_for_path with circular references"""
    
    # Create a dict with circular reference
    d = {}
    d['self'] = d
    d['key'] = 'value'
    
    # Test searching in circular structure
    path1 = pydantic.aliases.AliasPath('key')
    result = path1.search_dict_for_path(d)
    assert result == 'value'
    
    # Try to follow the circular reference
    path2 = pydantic.aliases.AliasPath('self', 'self', 'self', 'key')
    result2 = path2.search_dict_for_path(d)
    assert result2 == 'value'
    
    # This should work without infinite recursion
    path3 = pydantic.aliases.AliasPath('self', 'self', 'self', 'self', 'self', 'key')
    result3 = path3.search_dict_for_path(d)
    assert result3 == 'value'


@given(st.text())
def test_alias_generator_mutation_safety(field):
    """Test that AliasGenerator doesn't mutate the input string"""
    
    original = field
    original_copy = field
    
    def mutating_func(s: str) -> str:
        # This shouldn't actually mutate since strings are immutable
        return s.upper()
    
    gen = pydantic.aliases.AliasGenerator(
        alias=mutating_func,
        validation_alias=lambda s: s.lower(),
        serialization_alias=lambda s: s[::-1]
    )
    
    result = gen.generate_aliases(field)
    
    # Original should be unchanged
    assert field == original
    assert field is original_copy or field == original_copy


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=5),
            st.one_of(st.none(), st.text(), st.integers())
        ),
        min_size=1,
        max_size=10
    )
)
def test_alias_path_search_with_none_values(key_value_pairs):
    """Test search_dict_for_path when values in path are None"""
    
    # Build a dict from key-value pairs
    data = {k: v for k, v in key_value_pairs}
    
    # Test searching for keys with None values
    for key, value in key_value_pairs:
        path = pydantic.aliases.AliasPath(key)
        result = path.search_dict_for_path(data)
        
        # Should return the actual value, even if it's None
        assert result == value
        if value is None:
            assert result is None
            assert result != pydantic.aliases.PydanticUndefined


@given(st.data())
def test_alias_choices_mixed_types_stress(data):
    """Stress test AliasChoices with mixed types"""
    
    # Generate a mix of strings, integers, and AliasPath objects
    choices = []
    for _ in range(data.draw(st.integers(min_value=1, max_value=10))):
        choice_type = data.draw(st.integers(min_value=0, max_value=2))
        if choice_type == 0:
            choices.append(data.draw(st.text()))
        elif choice_type == 1:
            choices.append(data.draw(st.integers()))
        else:
            # AliasPath
            path_elements = data.draw(st.lists(
                st.one_of(st.text(min_size=1), st.integers()),
                min_size=1,
                max_size=3
            ))
            choices.append(pydantic.aliases.AliasPath(path_elements[0], *path_elements[1:]))
    
    alias_choices = pydantic.aliases.AliasChoices(choices[0], *choices[1:])
    
    # Verify all choices are preserved
    assert len(alias_choices.choices) == len(choices)
    
    # Test convert_to_aliases
    converted = alias_choices.convert_to_aliases()
    assert len(converted) == len(choices)
    
    for i, choice in enumerate(choices):
        if isinstance(choice, pydantic.aliases.AliasPath):
            assert converted[i] == choice.path
        else:
            assert converted[i] == [choice]


@given(st.text(min_size=1))
def test_alias_generator_with_raising_functions(field):
    """Test AliasGenerator when functions raise exceptions"""
    
    def always_raises(s: str) -> str:
        raise ValueError(f"Always fails for {s}")
    
    def sometimes_raises(s: str) -> str:
        if 'a' in s.lower():
            raise ValueError("Contains 'a'")
        return s.upper()
    
    gen = pydantic.aliases.AliasGenerator(
        alias=sometimes_raises,
        validation_alias=always_raises
    )
    
    try:
        result = gen.generate_aliases(field)
        # If it succeeded, alias function didn't raise
        assert 'a' not in field.lower()
        # But validation_alias should always raise
        assert False, "validation_alias should have raised"
    except ValueError:
        # Expected - one of the functions raised
        pass