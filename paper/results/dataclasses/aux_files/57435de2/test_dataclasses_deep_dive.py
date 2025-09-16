import dataclasses
from dataclasses import dataclass, field, asdict, astuple, replace, make_dataclass, fields, Field, MISSING
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import pytest
import keyword
from typing import Any
import sys
import copy


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
        st.recursive(
            st.one_of(
                st.integers(),
                st.text(max_size=10),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans()
            ),
            lambda children: st.one_of(
                st.lists(children, max_size=3),
                st.dictionaries(st.text(max_size=5), children, max_size=3),
                st.tuples(children, children)
            ),
            max_leaves=15
        ),
        min_size=1,
        max_size=5
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow], max_examples=50)
def test_asdict_deep_structures_mutation_isolation(field_dict):
    field_list = [(name, type(val)) for name, val in field_dict.items()]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**field_dict)
    
    dict_result1 = asdict(instance)
    dict_result2 = asdict(instance)
    
    def mutate_structure(obj):
        if isinstance(obj, list):
            if obj:
                obj.append("MUTATED")
        elif isinstance(obj, dict):
            obj["MUTATED_KEY"] = "MUTATED_VALUE"
    
    for key in dict_result1:
        mutate_structure(dict_result1[key])
    
    assert dict_result2 != dict_result1
    
    for name, original_val in field_dict.items():
        assert getattr(instance, name) == original_val


@given(
    st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
        min_size=1,
        max_size=10,
        unique=True
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_make_dataclass_with_field_objects(field_names):
    field_list = []
    for name in field_names:
        f = field(default=None, metadata={"test": True})
        field_list.append((name, int, f))
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls()
    
    for name in field_names:
        assert hasattr(instance, name)
        assert getattr(instance, name) is None
    
    retrieved_fields = fields(cls)
    for f in retrieved_fields:
        assert f.metadata == {"test": True}


@given(st.integers(), st.text())
def test_replace_on_frozen_dataclass(val, txt):
    @dataclass(frozen=True)
    class FrozenClass:
        value: int
        text: str
    
    instance = FrozenClass(value=val, text=txt)
    
    new_instance = replace(instance, value=val + 1)
    
    assert instance.value == val
    assert new_instance.value == val + 1
    assert new_instance.text == txt
    assert instance is not new_instance


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
        st.one_of(st.integers(), st.text(max_size=100)),
        min_size=1,
        max_size=10
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_fields_returns_field_objects(field_dict):
    field_list = [(name, type(val)) for name, val in field_dict.items()]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    retrieved_fields = fields(cls)
    
    for f in retrieved_fields:
        assert isinstance(f, Field)
        assert hasattr(f, 'name')
        assert hasattr(f, 'type')
        assert hasattr(f, 'default')
        assert hasattr(f, 'default_factory')
        assert hasattr(f, 'repr')
        assert hasattr(f, 'hash')
        assert hasattr(f, 'init')
        assert hasattr(f, 'compare')
        assert hasattr(f, 'metadata')


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
            st.one_of(st.integers(), st.text(max_size=100))
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_asdict_with_slots(field_specs):
    field_list = [(name, type(val)) for name, val in field_specs]
    
    try:
        cls = make_dataclass("TestClass", field_list, slots=True)
    except (TypeError, ValueError):
        return
    
    values = {name: val for name, val in field_specs}
    instance = cls(**values)
    
    dict_result = asdict(instance)
    
    assert dict_result == values
    
    assert not hasattr(instance, '__dict__')
    assert hasattr(instance, '__slots__')


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
        st.one_of(
            st.lists(st.integers(), min_size=1, max_size=3),
            st.dictionaries(st.text(max_size=5), st.integers(), min_size=1, max_size=3)
        ),
        min_size=1,
        max_size=5
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_asdict_preserves_collection_types(field_dict):
    field_list = [(name, type(val)) for name, val in field_dict.items()]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**field_dict)
    
    dict_result = asdict(instance)
    
    for name, original_val in field_dict.items():
        result_val = dict_result[name]
        assert type(result_val) == type(original_val)
        assert result_val == original_val
        
        if isinstance(original_val, (list, dict)):
            assert result_val is not original_val


@given(st.integers())
def test_dataclass_with_property(val):
    @dataclass
    class TestClass:
        _value: int = field(init=False, repr=False)
        
        @property
        def value(self):
            return self._value
        
        @value.setter
        def value(self, v):
            self._value = v
        
        def __init__(self, value: int):
            self._value = value
    
    instance = TestClass(value=val)
    assert instance.value == val
    
    dict_result = asdict(instance)
    assert "_value" in dict_result
    assert dict_result["_value"] == val


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
            st.one_of(st.integers(), st.text(max_size=100))
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_is_dataclass_function(field_specs):
    field_list = [(name, type(val)) for name, val in field_specs]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    assert is_dataclass(cls) == True
    
    values = {name: val for name, val in field_specs}
    instance = cls(**values)
    
    assert is_dataclass(instance) == True
    
    assert is_dataclass(int) == False
    assert is_dataclass(42) == False
    assert is_dataclass("string") == False


@given(
    st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
        min_size=1,
        max_size=10,
        unique=True
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_make_dataclass_namespace(field_names):
    namespace = {"custom_method": lambda self: "custom"}
    
    field_list = [(name, int, field(default=0)) for name in field_names]
    
    try:
        cls = make_dataclass("TestClass", field_list, namespace=namespace)
    except (TypeError, ValueError):
        return
    
    instance = cls()
    
    assert hasattr(instance, "custom_method")
    assert instance.custom_method() == "custom"


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
        st.recursive(
            st.one_of(st.integers(), st.text(max_size=10)),
            lambda children: st.lists(children, min_size=1, max_size=3),
            max_leaves=10
        ),
        min_size=1,
        max_size=5
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow], max_examples=30)
def test_astuple_deep_structures(field_dict):
    field_list = [(name, type(val)) for name, val in field_dict.items()]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**field_dict)
    
    tuple_result = astuple(instance)
    
    assert len(tuple_result) == len(field_dict)
    
    def check_deep_copy(original, copied):
        if isinstance(original, list):
            assert isinstance(copied, list)
            assert len(original) == len(copied)
            assert original is not copied
            for o, c in zip(original, copied):
                check_deep_copy(o, c)
        else:
            assert original == copied
    
    for i, (name, original_val) in enumerate(field_dict.items()):
        check_deep_copy(original_val, tuple_result[i])


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Ll"], whitelist_characters="_")).filter(lambda x: x.isidentifier() and not keyword.iskeyword(x)),
        st.sets(st.integers(), min_size=0, max_size=5),
        min_size=1,
        max_size=5
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_asdict_with_sets(field_dict):
    field_list = [(name, set) for name in field_dict]
    
    try:
        cls = make_dataclass("TestClass", field_list)
    except (TypeError, ValueError):
        return
    
    instance = cls(**{name: val.copy() for name, val in field_dict.items()})
    
    dict_result = asdict(instance)
    
    for name, original_set in field_dict.items():
        result_set = dict_result[name]
        
        assert isinstance(result_set, list)
        assert set(result_set) == original_set
        
        for item in result_set:
            assert item in original_set


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])