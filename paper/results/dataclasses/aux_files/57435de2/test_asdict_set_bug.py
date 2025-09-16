from dataclasses import dataclass, asdict
from hypothesis import given, strategies as st
import json
import pytest


@given(st.sets(st.integers(), min_size=0, max_size=10))
def test_asdict_with_sets_not_json_serializable(items):
    @dataclass
    class TestClass:
        my_set: set
    
    instance = TestClass(my_set=items)
    result = asdict(instance)
    
    assert isinstance(result['my_set'], set)
    
    with pytest.raises(TypeError, match="Object of type set is not JSON serializable"):
        json.dumps(result)


@given(
    st.sets(st.integers(), min_size=0, max_size=5),
    st.sets(st.text(max_size=10), min_size=0, max_size=5)
)
def test_nested_dataclass_with_sets(int_set, str_set):
    @dataclass
    class Inner:
        numbers: set
        strings: set
    
    @dataclass
    class Outer:
        inner: Inner
        own_set: set
    
    inner_obj = Inner(numbers=int_set, strings=str_set)
    outer_obj = Outer(inner=inner_obj, own_set={1, 2})
    
    result = asdict(outer_obj)
    
    assert isinstance(result['own_set'], set)
    assert isinstance(result['inner']['numbers'], set)
    assert isinstance(result['inner']['strings'], set)
    
    with pytest.raises(TypeError):
        json.dumps(result)


@given(st.frozensets(st.integers(), min_size=0, max_size=10))
def test_asdict_with_frozensets(items):
    @dataclass
    class TestClass:
        my_frozenset: frozenset
    
    instance = TestClass(my_frozenset=items)
    result = asdict(instance)
    
    assert isinstance(result['my_frozenset'], frozenset)
    
    with pytest.raises(TypeError, match="Object of type frozenset is not JSON serializable"):
        json.dumps(result)


def test_asdict_set_vs_list_dict_tuple():
    @dataclass
    class TestClass:
        my_list: list
        my_dict: dict
        my_tuple: tuple
        my_set: set
    
    instance = TestClass(
        my_list=[1, 2, 3],
        my_dict={'a': 1, 'b': 2},
        my_tuple=(1, 2, 3),
        my_set={1, 2, 3}
    )
    
    result = asdict(instance)
    
    assert isinstance(result['my_list'], list)
    assert isinstance(result['my_dict'], dict)
    assert isinstance(result['my_tuple'], list)
    assert isinstance(result['my_set'], set)
    
    assert result['my_list'] == [1, 2, 3]
    assert result['my_dict'] == {'a': 1, 'b': 2}
    assert result['my_tuple'] == [1, 2, 3]
    assert result['my_set'] == {1, 2, 3}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])