from dataclasses import dataclass, asdict
from hypothesis import given, strategies as st
import json
import pytest


@given(st.sets(st.one_of(st.integers(), st.text(max_size=10)), min_size=1, max_size=10))
def test_asdict_preserves_sets_breaking_json_contract(items):
    @dataclass
    class TestClass:
        data: set
    
    instance = TestClass(data=items)
    result = asdict(instance)
    
    assert isinstance(result['data'], set)
    assert result['data'] == items
    
    with pytest.raises(TypeError):
        json.dumps(result)


@given(st.frozensets(st.one_of(st.integers(), st.text(max_size=10)), min_size=1, max_size=10))
def test_asdict_preserves_frozensets_breaking_json_contract(items):
    @dataclass
    class TestClass:
        data: frozenset
    
    instance = TestClass(data=items)
    result = asdict(instance)
    
    assert isinstance(result['data'], frozenset)
    assert result['data'] == items
    
    with pytest.raises(TypeError):
        json.dumps(result)


@given(st.tuples(st.integers(), st.text(max_size=10), st.floats(allow_nan=False, allow_infinity=False)))
def test_asdict_preserves_tuples_allowing_json(items):
    @dataclass
    class TestClass:
        data: tuple
    
    instance = TestClass(data=items)
    result = asdict(instance)
    
    assert isinstance(result['data'], tuple)
    assert result['data'] == items
    
    try:
        json.dumps(result)
    except TypeError:
        pytest.fail("tuples are JSON serializable as arrays")


def test_mixed_collections_json_compatibility():
    @dataclass
    class DataWithCollections:
        list_field: list
        dict_field: dict
        tuple_field: tuple
        set_field: set
        frozenset_field: frozenset
    
    instance = DataWithCollections(
        list_field=[1, 2, 3],
        dict_field={'a': 1},
        tuple_field=(4, 5),
        set_field={6, 7},
        frozenset_field=frozenset({8, 9})
    )
    
    result = asdict(instance)
    
    json_compatible = {}
    json_incompatible = {}
    
    for key, value in result.items():
        try:
            json.dumps({key: value})
            json_compatible[key] = type(value).__name__
        except TypeError:
            json_incompatible[key] = type(value).__name__
    
    assert json_compatible == {
        'list_field': 'list',
        'dict_field': 'dict',
        'tuple_field': 'tuple'
    }
    
    assert json_incompatible == {
        'set_field': 'set',
        'frozenset_field': 'frozenset'
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])